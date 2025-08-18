import base64
import csv
import os
import re
from urllib.parse import urlparse

from django.contrib.gis.geos import Point

from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner
from territories.management.commands.geo_base_command import GeoBaseCommand
from territories.models import City, Department


class Command(GeoBaseCommand):
    help = "Import accommodations from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path of the CSV file to process (separator: ,)")
        parser.add_argument("--source", type=str, help="External source, see accommodation.models.ExternalSource")
        parser.add_argument("--skip-images", type=bool, default=False, help="Skip images import")

    def _get_or_create_city(self, city, postal_code):
        # normalize city name
        response = self.fetch_city_from_api(postal_code, city, strict_mode=True)
        if not response:
            return
        city = response["nom"] if response else city
        try:
            return City.objects.get(name__iexact=city, postal_codes__contains=[postal_code])
        except City.DoesNotExist:
            department_code = postal_code[:2]
            if postal_code.startswith("97") or postal_code.startswith("98"):
                department_code = postal_code[:3]

            city = City.objects.create(
                name=city, postal_codes=[postal_code], department=Department.objects.get(code=department_code)
            )
            return self.fill_city_from_api(city)

    def handle(self, *args, **options):
        def to_digit(value, can_be_zero=True):
            if not value:
                return
            cleaned_value = value.replace("€", "").strip()
            cleaned_value = cleaned_value.replace(",", ".")
            cleaned_value = cleaned_value.split(".")[0]
            cleaned_value = int(cleaned_value) if cleaned_value.isdigit() else None
            if not can_be_zero and cleaned_value == 0:
                return None
            return cleaned_value

        def to_bool(value):
            if not value:
                return
            return value.strip().lower() in ("oui", "vrai", "true", "1", "yes")

        csv_file_path = options["file"]
        source = options["source"]
        skip_images = options["skip_images"]

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            total_imported = 0

            owner = None
            for row in reader:
                if not owner:
                    parsed_url = urlparse(row["owner_url"])
                    owner_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    owner = Owner.get_or_create(data={"name": row["owner_name"], "url": owner_url})

                geom = (
                    Point(float(row["longitude"]), float(row["latitude"]))
                    if row["latitude"] and row["longitude"]
                    else None
                )

                pictures = re.split(r"\||\n", row["pictures"]) if row["pictures"] else []
                # NOTE: do not use set to keep order
                pictures = [url for i, url in enumerate(pictures) if url not in pictures[:i]]

                images_content = []
                images_urls = []
                for picture in pictures:
                    if picture.startswith("data:"):
                        base64_data = re.sub("^data:image/[^;]+;base64,", "", picture)
                        image_bytes = base64.b64decode(base64_data)
                        images_content.append(image_bytes)
                    elif picture.startswith("http"):
                        images_urls.append(picture)

                city = self._get_or_create_city(row["city"].strip(), row["postal_code"].strip())
                if not city:
                    self.stderr.write(
                        f"Could not get or create city {row['city']} for postal code {row['postal_code']}"
                    )
                    continue

                data = {
                    "name": row["name"].strip(),
                    "address": row["address"].strip(),
                    "city": city.name,
                    "postal_code": row["postal_code"].strip(),
                    "residence_type": row["residence_type"].strip(),
                    "nb_total_apartments": to_digit(row["nb_total_apartments"]),
                    "nb_accessible_apartments": to_digit(row["nb_accessible_apartments"]),
                    "nb_coliving_apartments": to_digit(row.get("nb_coliving_apartments", 0)),
                    "nb_t1": to_digit(row["nb_t1"]),
                    "nb_t1_bis": to_digit(row.get("nb_t1_bis", 0)),
                    "nb_t2": to_digit(row["nb_t2"]),
                    "nb_t3": to_digit(row.get("nb_t3", 0)),
                    "nb_t4_more": to_digit(row.get("nb_t4_more", 0)),
                    "price_min_t1": to_digit(row["t1_rent_min"], can_be_zero=False),
                    "price_max_t1": to_digit(row["t1_rent_max"], can_be_zero=False),
                    "price_min_t1_bis": to_digit(row.get("t1_bis_rent_min"), can_be_zero=False),
                    "price_max_t1_bis": to_digit(row.get("t1_bis_rent_max"), can_be_zero=False),
                    "price_min_t2": to_digit(row["t2_rent_min"], can_be_zero=False),
                    "price_max_t2": to_digit(row["t2_rent_max"], can_be_zero=False),
                    "price_min_t3": to_digit(row.get("t3_rent_min"), can_be_zero=False),
                    "price_max_t3": to_digit(row.get("t3_rent_max"), can_be_zero=False),
                    "price_min_t4_more": to_digit(row.get("t4_more_rent_min"), can_be_zero=False),
                    "price_max_t4_more": to_digit(row.get("t4_more_rent_max"), can_be_zero=False),
                    "laundry_room": to_bool(row["laundry_room"]),
                    "common_areas": to_bool(row["common_areas"]),
                    "bike_storage": to_bool(row["bike_storage"]),
                    "parking": to_bool(row["parking"]),
                    "secure_access": to_bool(row.get("secure_access")),
                    "residence_manager": to_bool(row.get("residence_manager")),
                    "kitchen_type": row["kitchen_type"].lower().strip().lower(),
                    "desk": to_bool(row.get("desk")),
                    "cooking_plates": to_bool(row.get("cooking_plates")),
                    "microwave": to_bool(row.get("microwave")),
                    "refrigerator": to_bool(row.get("refrigerator")),
                    "bathroom": row["bathroom"].lower().strip(),
                    "external_url": row["owner_url"].strip(),
                    "geom": geom,
                    "owner_id": owner.pk if owner else None,
                    "source_id": row.get("code"),
                    "source": source,
                }

                if not skip_images:
                    data["images_content"] = images_content
                    data["images_urls"] = images_urls

                serializer = AccommodationImportSerializer(data=data)

                if serializer.is_valid():
                    acc = serializer.save()
                    total_imported += 1
                    print(f"Successfully inserted {acc.name} - {acc.address}, available at {acc.get_absolute_url()}")
                else:
                    print(serializer.errors)

        self.stdout.write(self.style.SUCCESS(f"Import finished : {total_imported} imported"))
