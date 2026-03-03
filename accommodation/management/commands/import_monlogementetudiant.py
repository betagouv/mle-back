import json
import shutil
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand

from accommodation.models import Accommodation, ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner


class FakeSFTPDownloader:
    def __init__(self, stdout, fixture_file):
        self.stdout = stdout
        self.fixture_file = Path(fixture_file).expanduser()

    def download(self, remote_path):
        if not self.fixture_file.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.fixture_file}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            shutil.copyfile(self.fixture_file, temp_file.name)

        self.stdout.write(f"Fake SFTP download from {remote_path} completed using local fixture {self.fixture_file}.")
        return Path(temp_file.name)


class Command(BaseCommand):
    help = "Import Mon Logement Etudiant accommodations from a JSON file downloaded from SFTP."

    owner_name_by_brand = {
        "FACH": "FAC HABITAT",
    }
    residence_type = "residence-etudiante"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Local JSON file path to import directly.")
        parser.add_argument(
            "--fixture-file",
            type=str,
            default="~/Downloads/monlogementetudiant.json",
            help="Local file used by the fake SFTP downloader.",
        )
        parser.add_argument(
            "--remote-path",
            type=str,
            default="/exports/monlogementetudiant.json",
            help="Remote SFTP path used by the fake downloader for logging.",
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

    def _build_payload(self, item, owner):
        external_reference = str(item["id"])
        return {
            "name": item["name"].strip(),
            "address": item["address"].strip(),
            "city": item["city"].strip(),
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
            "source": ExternalSource.SOURCE_MON_LOGEMENT_ETUDIANT,
            "source_id": external_reference,
            **self._build_typology_values(item),
        }

    def _load_records(self, json_path):
        with Path(json_path).open(encoding="utf-8") as json_file:
            data = json.load(json_file)

        if not isinstance(data, list):
            raise ValueError("Expected a JSON array of accommodations.")

        return data

    def handle(self, *args, **options):
        json_path = options.get("file")
        should_cleanup = False

        if json_path:
            source_path = Path(json_path).expanduser()
        else:
            downloader = FakeSFTPDownloader(self.stdout, options["fixture_file"])
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
