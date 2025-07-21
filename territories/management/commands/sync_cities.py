from accommodation.models import Accommodation
from territories.management.commands.geo_base_command import GeoBaseCommand
from territories.models import City, Department


class Command(GeoBaseCommand):
    help = "Creates French cities with boroughs (Paris, Marseille, Lyon) including all old and new INSEE codes, and other details from the API."

    def handle(self, *args, **kwargs):
        cities_data = [
            {
                "name": "Paris",
                "postal_codes": [f"750{str(i).zfill(2)}" for i in range(1, 21)],
                "insee_codes": [f"751{str(i).zfill(2)}" for i in range(1, 21)] + ["75056"],
                "department_code": "75",
            },
            {
                "name": "Marseille",
                "postal_codes": [f"130{str(i).zfill(2)}" for i in range(1, 17)],
                "insee_codes": [f"132{str(i).zfill(2)}" for i in range(1, 17)] + ["13055"],
                "department_code": "13",
            },
            {
                "name": "Lyon",
                "postal_codes": ["69001", "69002", "69003", "69004", "69005", "69006", "69007", "69008", "69009"],
                "insee_codes": [
                    "69123",
                    "69124",
                    "69125",
                    "69126",
                    "69127",
                    "69128",
                    "69129",
                    "69130",
                    "69131",
                    "69381",
                    "69382",
                    "69383",
                    "69384",
                    "69385",
                    "69386",
                    "69387",
                    "69388",
                    "69389",
                ],
                "department_code": "69",
            },
        ]

        main_cities = []
        for city_data in cities_data:
            self.stdout.write(self.style.SUCCESS(f"✅ Creating city {city_data['name']}"))
            department, _ = Department.objects.get_or_create(
                code=city_data["department_code"], defaults={"name": f"Department {city_data['department_code']}"}
            )

            if City.objects.filter(name=city_data["name"]).exists():
                self.stdout.write(self.style.SUCCESS(f"✅ City {city_data['name']} already exists"))
                continue

            city, _ = City.objects.get_or_create(
                name=city_data["name"],
                defaults={
                    "postal_codes": city_data["postal_codes"],
                    "insee_codes": city_data["insee_codes"],
                    "department": department,
                    "slug": city_data["name"].lower().replace(" ", "-"),
                },
            )

            main_cities.append(city.pk)

            self.fill_city_from_api(city)

        for city in City.objects.exclude(pk__in=main_cities):
            self.fill_city_from_api(city)

        # find non created cities
        distinct_city_postal_codes = (
            Accommodation.objects.filter(published=True).values_list("city", "postal_code").distinct()
        )
        for city, postal_code in distinct_city_postal_codes:
            if not city or not postal_code:
                continue

            if City.objects.filter(postal_codes__contains=[postal_code]).exists():
                self.stdout.write(self.style.SUCCESS(f"✅ City {city} ({postal_code}) already exists"))
                continue
            self.stdout.write(self.style.WARNING(f"⚠️ No city found for {city} ({postal_code}). Will create it."))

            department_code = postal_code[:2]
            if postal_code.startswith("97") or postal_code.startswith("98"):
                department_code = postal_code[:3]

            response = self.fetch_city_from_api(postal_code, name=city, strict_mode=True)
            if not response:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ No real city found for {city} ({postal_code}). Will not create it.")
                )
                continue

            try:
                new_city = City.objects.create(
                    name=city, postal_codes=[postal_code], department=Department.objects.get(code=department_code)
                )
            except Department.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ No department found for {department_code}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"✅ Created city: {city} ({postal_code})"))
            self.fill_city_from_api(new_city)
