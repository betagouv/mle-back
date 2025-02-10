import csv
import requests
from django.core.management.base import BaseCommand
from territories.models import City
from io import StringIO

CSV_URL = "https://www.data.gouv.fr/fr/datasets/r/89956da9-5b9b-41d7-8703-18dbec4d54a2"


class Command(BaseCommand):
    help = "Updates the average rent per m² for cities using data from a CSV file."

    def handle(self, *args, **options):
        self.stdout.write(f"Downloading CSV file from {CSV_URL}")

        try:
            response = requests.get(CSV_URL, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Error downloading the file: {e}")
            return

        self.stdout.write("File downloaded successfully. Parsing CSV data.")
        csv_content = response.content.decode("latin1")
        csv_reader = csv.DictReader(StringIO(csv_content), delimiter=";", quotechar='"')

        update_count = 0

        for row in csv_reader:
            epci_code = row.get("EPCI")
            average_rent = row.get("loypredm2")

            if not epci_code or not average_rent:
                self.stderr.write(f"Skipping entry due to missing data: {row}")
                continue

            try:
                average_rent = float(average_rent.replace(",", "."))
            except ValueError:
                self.stderr.write(f"Invalid rent value for EPCI {epci_code}: {average_rent}")
                continue

            city = City.objects.filter(epci_code=epci_code).first()
            if city:
                city.average_rent = average_rent
                city.save()
                update_count += 1
                self.stdout.write(f"Updated {city.name} (EPCI {epci_code}) with rent {average_rent} €/m².")
            else:
                self.stderr.write(f"No city found for EPCI {epci_code}, skipping.")

        self.stdout.write(f"Update process completed. {update_count} cities updated.")
