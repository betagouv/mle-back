import csv
import os
import re

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from geopy.exc import GeocoderQueryError
from geopy.geocoders import BANFrance

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner


class Command(BaseCommand):
    help = "Import accommodations from Arpej CSV file. Its supposed to already have the API integration done"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path of the CSV file to process (separator: ,)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geolocator = BANFrance(timeout=10)

    def handle(self, *args, **options):
        csv_file_path = options["file"]
        source = ExternalSource.SOURCE_ARPEJ

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            total_imported = 0

            def to_digit(value):
                if not value:
                    return
                cleaned_value = value.replace("€", "").strip()
                cleaned_value = value.replace(",", ".")
                cleaned_value = value.split(".")[0]
                return int(cleaned_value) if cleaned_value.isdigit() else None

            def to_bool(value):
                if not value:
                    return
                return value.strip().lower() in ("oui", "vrai", "true", "1", "yes")

            owner = Owner.get_or_create({"name": "ARPEJ", "url": "https://www.arpej.fr/fr/"})
            for row in reader:
                full_address = f"{row.get('post_address')}, {row.get('post_zipcode')} {row.get('post_city')}"
                try:
                    location = self.geolocator.geocode(full_address)
                except GeocoderQueryError:
                    location = None

                if not location:
                    self.stderr.write(f"Could not geocode address: {full_address}")
                    continue

                city = location.raw["properties"]["city"]
                address = location.raw["properties"]["name"]
                postal_code = location.raw["properties"]["postcode"]

                geom = Point(location.longitude, location.latitude, srid=4326)

                pictures = re.split(r",|\n", row["URL"]) if row["URL"] else []
                pictures = list(set(pictures))
                images_content = []
                images_urls = []
                for picture in pictures:
                    picture = picture.strip()
                    if picture.startswith("data:"):
                        images_content.append(picture)
                    elif picture.startswith("http"):
                        images_urls.append(picture)

                serializer = AccommodationImportSerializer(
                    data={
                        "name": row["Title"].strip(),
                        "address": address,
                        "city": city,
                        "postal_code": postal_code,
                        "residence_type": "universitaire-conventionnee",
                        "common_areas": "work place" in row.get("les points fort").lower(),
                        "bike_storage": "bike park" in row.get("les points fort").lower(),
                        "secure_access": "interphone" in row.get("Votre Logement").lower(),
                        "residence_manager": "staff sur place" in row.get("les points fort").lower(),
                        "kitchen_type": "private" if "kitchenette" in row.get("Votre Logement").lower() else None,
                        "desk": "coin bureau" in row.get("Votre Logement").lower(),
                        "cooking_plates": "kitchenette" in row.get("Votre Logement").lower(),
                        "refrigerator": "avec réfrigérateur" in row.get("Votre Logement").lower(),
                        "bathroom": "private" if "salle d'eau privative" in row.get("Votre Logement").lower() else None,
                        "images_content": images_content,
                        "images_urls": images_urls,
                        "external_url": row["URL ARPEJ.FR"].strip(),
                        "geom": geom,
                        "owner_id": owner.pk,
                        "source_id": row.get("IBAIL id"),
                        "source": source,
                    }
                )

                if serializer.is_valid():
                    acc = serializer.save()
                    total_imported += 1
                    print(f"Successfully inserted {acc.name} - {acc.address}")
                else:
                    print(serializer.errors)

        self.stdout.write(self.style.SUCCESS(f"Import finished : {total_imported} imported"))
