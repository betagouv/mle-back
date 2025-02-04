import requests

from territories.management.commands.geo_base_command import GeoBaseCommand
from territories.models import City, Department


class Command(GeoBaseCommand):
    help = "Creates French cities with boroughs (Paris, Marseille, Lyon) including all old and new INSEE codes, and other details from the API."

    def _fetch_city_from_api(self, code):
        base_api_url = "https://geo.api.gouv.fr/communes/"
        returned_fields = "&fields=nom,codesPostaux,codeDepartement,contour,codeEpci,population&format=json"

        response = requests.get(f"{base_api_url}?codePostal={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        print(f"Cannot found city with postal code {code}, assuming we have an insee code here.")

        response = requests.get(f"{base_api_url}?code={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        print(f"Cannot found city with insee code {code}")
        return

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
            department, _ = Department.objects.get_or_create(
                code=city_data["department_code"], defaults={"name": f"Department {city_data['department_code']}"}
            )

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

            self._fill_from_api(city)

        for city in City.objects.exclude(pk__in=main_cities):
            self._fill_from_api(city)

    def _fill_from_api(self, city):
        response = self.fetch_city_from_api(city.postal_codes[0])
        if response:
            city.boundary = self.geojson_mpoly(response["contour"])
            city.epci_code = response.get("codeEpci")
            city.population = response.get("population", 0)
            city.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✔️ {city.name} created/updated with INSEE {city.insee_codes}, boundary, epci_code and population"
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Unable to fetch detailed info for {city.name}"))
