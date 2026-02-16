from collections import defaultdict
import os
import csv

from django.core.management.base import BaseCommand
from django.db.models import Func, Value

from accommodation.models import Accommodation


class Command(BaseCommand):
    help = "Import Crous prices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving",
        )

    def handle(self, *args, **options):
        csv_file_path = "import_crous_prices.csv"

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        dry_run = options["dry_run"]

        data_by_residence = self.get_data_by_residence(csv_file_path)

        total_updated = 0
        for name, vals in data_by_residence.items():
            print("Managing", name)
            acc_instance = (
                Accommodation.objects.annotate(unaccent_name=Func("name", function="unaccent"))
                .filter(unaccent_name__iexact=Func(Value(name), function="unaccent"))
                .first()
            )
            if not acc_instance:
                self.stderr.write(self.style.WARNING(f"Accommodation not found: {name}, skipping"))
                continue

            self.update_accommodation(acc_instance, vals, dry_run)
            total_updated += 1
        self.stdout.write(self.style.SUCCESS(f"Import finished: {total_updated} residences updated"))

    def update_accommodation(self, acc_instance: Accommodation, vals: dict, dry_run: bool) -> None:
        for key in vals.keys():
            setattr(acc_instance, key, vals[key])
        if not dry_run:
            acc_instance.save()
        print(f"{acc_instance} updated with {vals}")
        return acc_instance

    def get_data_by_residence(self, csv_file_path: str) -> dict:
        data_by_residence = defaultdict(
            lambda: {
                "price_min_t1": 0,
                "price_max_t1": 0,
                "price_min_t1_bis": 0,
                "price_max_t1_bis": 0,
                "price_min_t2": 0,
                "price_max_t2": 0,
                "price_min_t3": 0,
                "price_max_t3": 0,
                "price_min_t4": 0,
                "price_max_t4": 0,
                "price_min_t5": 0,
                "price_max_t5": 0,
                "price_min_t6": 0,
                "price_max_t6": 0,
                "price_min_t7_more": 0,
                "price_max_t7_more": 0,
            }
        )

        def normalize_type(t):
            return t.strip().upper().replace("É", "E").replace("È", "E")

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                res_name = row["Residence"].strip()
                type_logement = normalize_type(row["nom_lgt"])

                entry = data_by_residence[res_name]
                if "T1 BIS" in type_logement:
                    entry["price_min_t1_bis"] = row["loyer_min"]
                    entry["price_max_t1_bis"] = row["loyer_max"]
                elif any(t in type_logement for t in ["T1", "STUDIO", "STUDETTE", "APPART", "CHAMBRE"]):
                    entry["price_min_t1"] = row["loyer_min"]
                    entry["price_max_t1"] = row["loyer_max"]
                elif "T2" in type_logement:
                    entry["price_min_t2"] = row["loyer_min"]
                    entry["price_max_t2"] = row["loyer_max"]
                elif "T3" in type_logement:
                    entry["price_min_t3"] = row["loyer_min"]
                    entry["price_max_t3"] = row["loyer_max"]
                elif "T4" in type_logement:
                    entry["price_min_t4"] = row["loyer_min"]
                    entry["price_max_t4"] = row["loyer_max"]
                elif "T5" in type_logement:
                    entry["price_min_t5"] = row["loyer_min"]
                    entry["price_max_t5"] = row["loyer_max"]
                elif "T6" in type_logement:
                    entry["price_min_t6"] = row["loyer_min"]
                    entry["price_max_t6"] = row["loyer_max"]
                elif any(t in type_logement for t in ["T7", "T8", "T9"]):
                    entry["price_min_t7_more"] = row["loyer_min"]
                    entry["price_max_t7_more"] = row["loyer_max"]
                else:
                    print("non mapped type", type_logement)
        return data_by_residence
