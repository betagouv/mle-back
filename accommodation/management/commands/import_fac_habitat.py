import json
from pathlib import Path

from django.conf import settings
from territories.management.commands.geo_base_command import GeoBaseCommand

from accommodation.factories import get_sftp_downloader
from accommodation.models import Accommodation, ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from django.contrib.gis.geos import Point
from account.models import Owner

# TODO : add this command to the cron.json file
# {
#     "command": "0 2 * * * python manage.py import_fac_habitat"
# }


class Command(GeoBaseCommand):
    help = "Import Mon Logement Etudiant accommodations from a JSON file downloaded from SFTP."

    owner_name_by_brand = {
        "FACH": "FAC HABITAT",
    }
    residence_type = "residence-etudiante"

    def __init__(self, *args, sftp_downloader_factory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sftp_downloader_factory = sftp_downloader_factory or get_sftp_downloader

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Local JSON file path to import directly.")
        parser.add_argument(
            "--sftp-mode",
            type=str,
            choices=("fake", "real"),
            default="real",
            help="Select the SFTP downloader implementation.",
        )
        parser.add_argument(
            "--fixture-file",
            type=str,
            default="~/Downloads/monlogementetudiant.json",
            help="Local file used by the fake SFTP downloader implementation.",
        )
        parser.add_argument(
            "--remote-path",
            type=str,
            default=getattr(settings, "FAC_HABITAT_SFTP_REMOTE_PATH", "/export/monlogementetudiant.json"),
            help="Remote SFTP path used by the selected downloader.",
        )

    @staticmethod
    def _to_int(value):
        if value in (None, ""):
            return None
        return int(float(value))

    @staticmethod
    def _to_bool(value):
        if value in (None, ""):
            return None
        return bool(value)

    def _get_owner(self, brand):
        owner_name = self.owner_name_by_brand.get(brand, brand or "Mon Logement Etudiant")
        return Owner.get_or_create({"name": owner_name})

    def _build_typology_values(self, item):
        typology_groups = {
            "t1": [("nb_t1", "t1_rent_min", "t1_rent_max")],
            "t1_bis": [
                ("nb_t1_bis", "t1_bis_rent_min", "t1_bis_rent_max"),
                ("nb_t1_prime", "t1_prime_rent_min", "t1_prime_rent_max"),
                ("nb_studio_double", "studio_double_rent_min", "studio_double_rent_max"),
            ],
            "t2": [
                ("nb_t2", "t2_rent_min", "t2_rent_max"),
                ("nb_t2_duplex", "t2_duplex_rent_min", "t2_duplex_rent_max"),
                ("nb_duplex", "duplex_rent_min", "duplex_rent_max"),
            ],
            "t3": [
                ("nb_t3", "t3_rent_min", "t3_rent_max"),
                ("nb_duo", "duo_rent_min", "duo_rent_max"),
            ],
            "t4": [("nb_t4", "t4_rent_min", "t4_rent_max")],
            "t5": [
                ("nb_t5", "t5_rent_min", "t5_rent_max"),
                ("nb_t5_en_colocation", "t5_en_colocation_rent_min", "t5_en_colocation_rent_max"),
            ],
        }

        values = {}
        for typology, sources in typology_groups.items():
            counts = []
            min_prices = []
            max_prices = []
            for count_key, min_key, max_key in sources:
                count = self._to_int(item.get(count_key))
                if count is not None:
                    counts.append(count)

                min_price = self._to_int(item.get(min_key))
                if min_price is not None:
                    min_prices.append(min_price)

                max_price = self._to_int(item.get(max_key))
                if max_price is not None:
                    max_prices.append(max_price)

            values[f"nb_{typology}"] = sum(counts) if counts else None
            values[f"price_min_{typology}"] = min(min_prices) if min_prices else None
            values[f"price_max_{typology}"] = max(max_prices) if max_prices else None

        return values

    def _fix_city_name(self, city_name):
        if city_name == "Montfavet":
            return "Avignon"
        if city_name == "Pierrefitte-sur-Seine":
            return "Saint-Denis"
        if city_name == "Toulon - la valette":
            return "La Valette-du-Var"
        return city_name

    def _build_payload(self, item, owner):
        external_reference = str(item["id"])

        item["city"] = self._fix_city_name(item["city"])

        point = self._geocode(f"{item['address']}, {item['city']}, {item['postal_code']}")

        if not point:
            self.stderr.write(f"Could not geocode address: {item['address']}, {item['city']}, {item['postal_code']}")
            return None

        geom = Point(point.longitude, point.latitude, srid=4326)

        city = self._get_or_create_city(item["city"].strip(), item["postal_code"].strip())
        if not city:
            self.stderr.write(f"Could not get or create city {item['city']} for postal code {item['postal_code']}")
            return None

        return {
            "name": item["name"].strip(),
            "address": item["address"].strip(),
            "city": city.name,
            "postal_code": str(item["postal_code"]).strip(),
            "residence_type": self.residence_type,
            "target_audience": "etudiants",
            "accept_waiting_list": self._to_bool(item.get("accept_waiting_list")),
            "laundry_room": self._to_bool(item.get("laundry_room")),
            "parking": self._to_bool(item.get("parking")),
            "residence_manager": self._to_bool(item.get("residence_manager")),
            "kitchen_type": item.get("kitchen_type"),
            "refrigerator": self._to_bool(item.get("refrigerator")),
            "bathroom": item.get("bathroom"),
            "nb_accessible_apartments": self._to_int(item.get("nb_accessible_apartments")),
            "nb_coliving_apartments": self._to_int(item.get("nb_coliving_apartments")),
            "nb_total_apartments": self._to_int(item.get("nb_total_apartments")),
            "external_reference": external_reference,
            "owner_id": owner.pk,
            "source": ExternalSource.SOURCE_FAC_HABITAT,
            "source_id": external_reference,
            "geom": geom,
            **self._build_typology_values(item),
        }

    def _load_records(self, json_path):
        with Path(json_path).open(encoding="utf-8") as json_file:
            data = json.load(json_file)

        if not isinstance(data, list):
            raise ValueError("Expected a JSON array of accommodations.")

        return data

    def _get_sftp_downloader(self, options):
        return self.sftp_downloader_factory(
            stdout=self.stdout,
            mode=options["sftp_mode"],
            fixture_file=options["fixture_file"],
        )

    def handle(self, *args, **options):
        json_path = options.get("file")
        should_cleanup = False

        if json_path:
            source_path = Path(json_path).expanduser()
        else:
            downloader = self._get_sftp_downloader(options)
            source_path = downloader.download(options["remote_path"])
            should_cleanup = True

        try:
            records = self._load_records(source_path)
        finally:
            if should_cleanup and source_path.exists():
                source_path.unlink()

        created_count = 0
        updated_count = 0

        for item in records:
            owner = self._get_owner(item.get("marque"))
            payload = self._build_payload(item, owner)
            if not payload:
                continue
            accommodation = Accommodation.objects.filter(
                owner=owner,
                external_reference=payload["external_reference"],
            ).first()

            serializer = AccommodationImportSerializer(
                instance=accommodation, data=payload, partial=bool(accommodation)
            )

            if not serializer.is_valid():
                self.stderr.write(f"Error importing {payload['external_reference']}: {serializer.errors}")
                continue

            serializer.save()
            if accommodation:
                updated_count += 1
            else:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished: {created_count} created, {updated_count} updated, {len(records)} processed."
            )
        )
