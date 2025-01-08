import csv
import json

import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand
from django.db.models import Q

from accommodation.models import Accommodation, ExternalSource
from territories.models import City, Department

TO_IGNORE = ("a définir", "nc", "-", "x", "?")
RESIDENCE_TYPE_MAPPING = {label: key for key, label in Accommodation.RESIDENCE_TYPE_CHOICES}


def geojson_mpoly(geojson):
    mpoly = GEOSGeometry(geojson if isinstance(geojson, str) else json.dumps(geojson))
    if isinstance(mpoly, MultiPolygon):
        return mpoly
    if isinstance(mpoly, Polygon):
        return MultiPolygon([mpoly])
    raise TypeError(f"{mpoly.geom_type} not acceptable for this model")


class Command(BaseCommand):
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

    def _fetch_city_from_api(self, code):
        base_api_url = "https://geo.api.gouv.fr/communes/"
        returned_fields = "&fields=nom,codesPostaux,codeDepartement,contour&format=json"

        response = requests.get(f"{base_api_url}?codePostal={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        # NOTE: this is a dirty workaround, data stored in CLEF is not clean, we can have postal or insee code in same field
        print(f"Cannot found city with postal code {code}, assuming we have an insee code here.")

        response = requests.get(f"{base_api_url}?code={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        print(f"Cannot found city with insee code {code}")
        return

    def _ensure_city_created(self, row):
        if self.skip_cities:
            return

        city = City.objects.filter(
            Q(postal_codes__contains=[row.get("Code postal")]) | Q(insee_code=row.get("Code postal"))
        ).first()
        if city:
            return

        response = self._fetch_city_from_api(row.get("Code postal"))
        if not response:
            return

        city = City.objects.create(
            name=response["nom"],
            boundary=geojson_mpoly(response["contour"]),
            postal_codes=response["codesPostaux"],
            department=Department.objects.get(code=response["codeDepartement"]),
            insee_code=response["code"],
        )
        if self.should_write:
            city.save()
            print(f"City {city} created")
        else:
            print(f"Would have created city {city}")
