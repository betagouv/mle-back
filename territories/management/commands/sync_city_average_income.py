import csv

from django.core.management.base import BaseCommand

from territories.models import City


class Command(BaseCommand):
    help = "Sync average income per city, according to INSEE stats, source: https://www.insee.fr/fr/statistiques/7752770?sommaire=7756859#tableau-figure1_radio2"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path of the CSV file to process (separator: ,)",
        )

    def handle(self, *args, **options):
        self.input_file = options.get("file")

        self.stdout.write(f"Reading {self.input_file}")

        with open(self.input_file, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not ((average_income := row.get("Niveau de vie médian")) and (epci_code := row["EPCI"])):
                    continue

                City.objects.filter(epci_code=epci_code).update(average_income=average_income)
                self.stdout.write(f"Updated cities with EPCI: {epci_code} (Average Income: {average_income})")

        self.stdout.write("Average income data import completed!")
