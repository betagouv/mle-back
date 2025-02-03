import csv

from django.contrib.gis.geos import Point
from django.db.models import Q

from accommodation.models import Accommodation, ExternalSource
from territories.management.commands.geo_base_command import GeoBaseCommand
from territories.models import City, Department

TO_IGNORE = ("a définir", "nc", "-", "x", "?")
RESIDENCE_TYPE_MAPPING = {label: key for key, label in Accommodation.RESIDENCE_TYPE_CHOICES}


class Command(GeoBaseCommand):
    help = "Import CLEF data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path of the CSV file to process (separator: ,)",
        )
        parser.add_argument("--write", action="store_true", help="Actually edit the database", default=False)
        parser.add_argument("--skip-cities", action="store_true", help="Skip management of cities", default=False)

    def handle(self, *args, **options):
        self.input_file = options.get("file")
        self.should_write = options["write"]
        self.skip_cities = options["skip_cities"]

        with open(self.input_file, "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for i, row in enumerate(reader):
                if (name := row["Nom de la résidence"]) == "Nom de la résidence":
                    # header is repeated in the file, ignoring the line
                    continue

                print(f"~ Processing line {i}")
                source_id = row["Identifiant fonctionnel"]

                accommodation = Accommodation.objects.filter(
                    sources__source=ExternalSource.SOURCE_CLEF, sources__source_id=source_id
                ).first()

                if not accommodation:
                    accommodation = Accommodation(name=name)

                for attr_db, attr_clef in [
                    ("city", "Commune"),
                    ("postal_code", "Code postal"),
                    ("owner_name", "Gestionnaire - Nom"),
                    ("owner_url", "Gestionnaire - Site"),
                    ("nb_total_apartments", "Nombre total de logements"),
                    ("nb_accessible_apartments", "Nombre de logements PMR"),
                    ("nb_coliving_apartments", "Nombre de logements en collocation"),
                    ("nb_t1", "T1"),
                    ("nb_t1_bis", "T1 bis"),
                    ("nb_t2", "T2"),
                    ("nb_t3", "T3"),
                    ("nb_t4_more", "T4 et plus"),
                ]:
                    value = row.get(attr_clef) or ""
                    if not value or value.lower() in TO_IGNORE:
                        continue

                    setattr(accommodation, attr_db, value)

                accommodation.address = row.get("Adresse administrative") or row.get("Adresse géolocalisée")

                if (latitude := row.get("Latitude")) and (longitude := row.get("Longitude")):
                    try:
                        accommodation.geom = Point(
                            float(longitude.replace(",", ".")), float(latitude.replace(",", ".")), srid=4326
                        )
                    except ValueError:
                        print("Invalid latitude/longitude values. Ignoring geom...")

                residence_type_clef = row.get("Type de résidence", "").strip()
                if residence_type_clef:
                    accommodation.residence_type = RESIDENCE_TYPE_MAPPING.get(residence_type_clef)

                accommodation.published = row.get("Statut de la résidence").lower() == "en service"

                self._ensure_city_created(row)

                if self.should_write:
                    accommodation.save()
                    print(f"{accommodation} saved (published = {accommodation.published})")
                else:
                    print(f"Would have save {accommodation.__dict__} and manage external sources {source_id}")
                    continue

                external_source, created = ExternalSource.objects.get_or_create(
                    accommodation=accommodation,
                    source=ExternalSource.SOURCE_CLEF,
                )
                if not created:
                    continue

                external_source.source_id = source_id
                external_source.save()
                print(f"ExternalSource {external_source} saved")

    def _ensure_city_created(self, row):
        if self.skip_cities:
            return

        postal_code = row.get("Code postal")
        if not postal_code:
            return

        city = City.objects.filter(
            Q(postal_codes__contains=[postal_code]) | Q(insee_codes__contains=[postal_code])
        ).first()

        if city:
            response = self.fetch_city_from_api(postal_code)
            if response and response["code"] not in city.insee_codes:
                city.insee_codes.append(response["code"])
                city.save()
                print(f"Updated city {city} with new INSEE code {response['code']}")
            return

        response = self.fetch_city_from_api(postal_code)
        if not response:
            return

        city = City.objects.create(
            name=response["nom"],
            boundary=self.geojson_mpoly(response["contour"]),
            postal_codes=response.get("codesPostaux", []),
            department=Department.objects.get(code=response["codeDepartement"]),
            insee_codes=[response["code"]],
            epci_code=response.get("codeEpci"),
            population=response.get("population", 0),
        )
        if self.should_write:
            city.save()
            print(f"City {city} created")
        else:
            print(f"Would have created city {city}")
            print(f"Would have created city {city}")
