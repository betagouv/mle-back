import csv
import os

import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner


class Command(BaseCommand):
    help = "Import accommodations from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path of the CSV file to process (separator: ,)")

    def handle(self, *args, **options):
        csv_file_path = options["file"]

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
                return int(cleaned_value) if cleaned_value.isdigit() else None

            def to_bool(value):
                return value.strip().lower() in ("vrai", "true", "1", "yes")

            def to_base64(values):
                images = []
                for value in values:
                    if value.startswith("data:"):
                        images.append(value)
                    elif value.startswith("http"):
                        image_response = requests.get(value)

                        if image_response.status_code == 200:
                            images.append(image_response.content)
                return images

            owner = Owner.get_or_create(data={"name": "Espacil", "url": "https://www.espacil-habitat.fr"})
            for row in reader:
                geom = (
                    Point(float(row["longitude"]), float(row["latitude"]))
                    if row["latitude"] and row["longitude"]
                    else None
                )

                serializer = AccommodationImportSerializer(
                    data={
                        "name": row["name"].strip(),
                        "address": row["address"].strip(),
                        "city": row["city"].strip(),
                        "postal_code": row["postal_code"].strip(),
                        "residence_type": row["residence_type"].strip(),
                        "nb_total_apartments": to_digit(row["nb_total_apartments"]),
                        "nb_accessible_apartments": to_digit(row["nb_accessible_apartments"]),
                        "nb_coliving_apartments": to_digit(row["nb_coliving_apartments"]),
                        "nb_t1": to_digit(row["nb_t1"]),
                        "nb_t1_bis": to_digit(row["nb_t1_bis"]),
                        "nb_t2": to_digit(row["nb_t2"]),
                        "nb_t3": to_digit(row["nb_t3"]),
                        "nb_t4_more": to_digit(row["nb_t4_more"]),
                        "price_min_t1": to_digit(row["t1_rent_min"]),
                        "price_max_t1": to_digit(row["t1_rent_max"]),
                        "price_min_t1_bis": to_digit(row["t1_bis_rent_min"]),
                        "price_max_t1_bis": to_digit(row["t1_bis_rent_max"]),
                        "price_min_t2": to_digit(row["t2_rent_min"]),
                        "price_max_t2": to_digit(row["t2_rent_max"]),
                        "price_min_t3": to_digit(row["t3_rent_min"]),
                        "price_max_t3": to_digit(row["t3_rent_max"]),
                        "price_min_t4_more": to_digit(row["t4_more_rent_min"]),
                        "price_max_t4_more": to_digit(row["t4_more_rent_max"]),
                        "laundry_room": to_bool(row["laundry_room"]),
                        "common_areas": to_bool(row["common_areas"]),
                        "bike_storage": to_bool(row["bike_storage"]),
                        "parking": to_bool(row["parking"]),
                        "secure_access": to_bool(row["secure_access"]),
                        "residence_manager": to_bool(row["residence_manager"]),
                        "kitchen_type": row["kitchen_type"].strip().lower(),
                        "desk": to_bool(row["desk"]),
                        "cooking_plates": to_bool(row["cooking_plates"]),
                        "microwave": to_bool(row["microwave"]),
                        "refrigerator": to_bool(row["refrigerator"]),
                        "bathroom": row["bathroom"].strip(),
                        "images": row["pictures"].split("|") if row["pictures"] else [],
                        "external_url": row["owner_url"].strip(),
                        "geom": geom,
                        "owner": owner,
                        "source_id": row["code"],
                        "source": ExternalSource.SOURCE_ESPACIL,
                    }
                )

                if serializer.is_valid():
                    serializer.save()
                    total_imported += 1
                else:
                    print(serializer.errors)

        self.stdout.write(self.style.SUCCESS(f"Import finished : {total_imported} imported"))
