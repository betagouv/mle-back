import csv
import os

from django.contrib.gis.geos import Point

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner
from territories.management.commands.geo_base_command import GeoBaseCommand


class Command(GeoBaseCommand):
    help = "Import accommodations from CROUS CSV file"

    def _parse_description(self, description):
        description = description.lower()
        attributes = {}
        if "laverie" in description:
            attributes["laundry_room"] = True
        if any(keyword in description for keyword in ["babyfoot", "ping-pong", "salle de sport"]):
            attributes["common_areas"] = True
        if "vélo" in description:
            attributes["bike_storage"] = True
        if "parking" in description:
            attributes["parking"] = True
        if any(keyword in description for keyword in ["badge", "accès sécurisé", "visiophone", "interphone"]):
            attributes["secure_access"] = True
        if "gardien" in description:
            attributes["residence_manager"] = True
        if any(keyword in description for keyword in ["kitchenette"]):
            attributes["kitchen_type"] = "private"
        if "bureau" in description:
            attributes["desk"] = True
        if "plaque de cuisson" in description:
            attributes["cooking_plates"] = True
        if "micro-ondes" in description:
            attributes["microwave"] = True
        if any(keyword in description for keyword in ["réfrigérateur", "frigo", "congélateur"]):
            attributes["refrigerator"] = True
        if any(keyword in description for keyword in ["salle de bain", "baignoire", "douche"]):
            attributes["bathroom"] = "private"
        return attributes

    def handle(self, *args, **options):
        csv_file_path = "crous_accommodations.csv"
        source = ExternalSource.SOURCE_CROUS

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        total_imported = 0

        owner = Owner.get_or_create(
            {
                "name": "CROUS",
                "url": "https://www.lescrous.fr/",
            }
        )

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                try:
                    lon = float(row["longitude"].replace(",", "."))
                    lat = float(row["latitude"].replace(",", "."))
                except ValueError:
                    self.stderr.write(f"Invalid coordinates for {row['nom_residence']}")
                    continue

                geom = Point(lon, lat, srid=4326)

                location = self._geocode(row["adresse_residence"])
                if not location:
                    self.stderr.write(f"Could not geocode address: {row['adresse_residence']}")
                    continue

                city = location.raw["properties"]["city"]
                postal_code = location.raw["properties"]["postcode"]
                city_obj = self._get_or_create_city(city, postal_code)
                address = location.raw["properties"]["name"]
                if not city_obj:
                    self.stderr.write(f"Could not get or create city {city} for postal code {postal_code}")
                    continue

                data = {
                    "name": row["nom_residence"].strip(),
                    "address": address,
                    "city": city_obj.name,
                    "postal_code": postal_code,
                    "residence_type": "universitaire-conventionnee",
                    "geom": geom,
                    "owner_id": owner.pk,
                    "source_id": row["code_residence"],
                    "source": source,
                    **self._parse_description(row["description_residence"]),
                }

                serializer = AccommodationImportSerializer(data=data)

                if serializer.is_valid():
                    acc = serializer.save()
                    total_imported += 1
                    self.stdout.write(self.style.SUCCESS(f"Imported: {acc.name} ({acc.city})"))
                else:
                    self.stderr.write(f"Error: {serializer.errors}")

        self.stdout.write(self.style.SUCCESS(f"Import finished: {total_imported} imported"))
