import csv
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Func, Value

from accommodation.models import Accommodation
from accommodation.serializers import AccommodationImportSerializer


class Command(BaseCommand):
    help = "Import CROUS nb accommodations from a CSV file and aggregate by residence"

    def handle(self, *args, **options):
        csv_file_path = "crous_nb_and_photos.csv"

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        def normalize_type(t):
            return t.strip().upper().replace("É", "E").replace("È", "E")

        data_by_residence = defaultdict(
            lambda: {
                "nb_total": 0,
                "nb_accessible": 0,
                "nb_coliving": 0,
                "nb_t1": 0,
                "nb_t1_bis": 0,
                "nb_t2": 0,
                "nb_t3": 0,
                "nb_t4": 0,
                "nb_t5": 0,
                "nb_t6": 0,
                "nb_t7_more": 0,
            }
        )

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                res_name = row["Residence"].strip()
                nb_logements = int(row["Nb Logement"])
                type_logement = normalize_type(row["Type Logement"])

                entry = data_by_residence[res_name]
                entry["nb_total"] += nb_logements

                if "PMR" in type_logement:
                    entry["nb_accessible"] += nb_logements

                if any(t in type_logement for t in ["PARTAG", "COLOC"]):
                    entry["nb_coliving"] += nb_logements

                if "T1 BIS" in type_logement:
                    entry["nb_t1_bis"] += nb_logements
                elif any(t in type_logement for t in ["T1", "STUDIO", "STUDETTE", "APPART", "CHAMBRE"]):
                    entry["nb_t1"] += nb_logements
                elif "T2" in type_logement:
                    entry["nb_t2"] += nb_logements
                elif "T3" in type_logement:
                    entry["nb_t3"] += nb_logements
                elif "T4" in type_logement:
                    entry["nb_t4"] += nb_logements
                elif "T5" in type_logement:
                    entry["nb_t5"] += nb_logements
                elif "T6" in type_logement:
                    entry["nb_t6"] += nb_logements
                elif any(t in type_logement for t in ["T7", "T8", "T9"]):
                    entry["nb_t7_more"] += nb_logements
                else:
                    print("non mapped type", type_logement)

        total_imported = 0

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

            serializer = AccommodationImportSerializer(
                instance=acc_instance,
                data={
                    "nb_total_apartments": vals["nb_total"],
                    "nb_accessible_apartments": vals["nb_accessible"],
                    "nb_coliving_apartments": vals["nb_coliving"],
                    "nb_t1": vals["nb_t1"],
                    "nb_t1_bis": vals["nb_t1_bis"],
                    "nb_t2": vals["nb_t2"],
                    "nb_t3": vals["nb_t3"],
                    "nb_t4": vals["nb_t4"],
                    "nb_t5": vals["nb_t5"],
                    "nb_t6": vals["nb_t6"],
                    "nb_t7_more": vals["nb_t7_more"],
                },
                partial=True,
            )

            if serializer.is_valid():
                serializer.save()
                total_imported += 1
                self.stdout.write(self.style.SUCCESS(f"Updated {acc_instance.name} ({vals['nb_total']} logements)"))
            else:
                self.stderr.write(self.style.ERROR(f"Error for {name}: {serializer.errors}"))
        self.stdout.write(self.style.SUCCESS(f"Import finished: {total_imported} residences imported"))
