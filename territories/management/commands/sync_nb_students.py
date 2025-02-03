import json
import requests
from django.core.management.base import BaseCommand
from territories.models import City


class Command(BaseCommand):
    help = "Updates the number of students per city using data from a JSON file available online."

    def handle(self, *args, **options):
        url = "https://data.enseignementsup-recherche.gouv.fr/api/explore/v2.1/catalog/datasets/fr-esr-atlas_regional-effectifs-d-etudiants-inscrits_agregeables/exports/json"
        self.stdout.write(f"Downloading file from {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Error downloading the file: {e}")
            return

        self.stdout.write("File downloaded successfully. Parsing JSON data.")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.stderr.write(f"Error decoding JSON data: {e}")
            return

        self.stdout.write("Resetting student count for all cities.")
        City.objects.update(nb_students=0)

        for entry in data:
            if entry.get("annee_universitaire") != "2023-24":
                continue

            insee_code = entry.get("com_id")
            nb_students = entry.get("effectif")

            if not insee_code or not nb_students:
                self.stderr.write(f"Skipping entry due to missing data: {entry}")
                continue

            city = City.objects.filter(name=entry.get("com_nom"), department__name=entry.get("dep_nom")).first()
            if not city:
                city = City.objects.filter(insee_codes__contains=[insee_code]).first()
                if not city:
                    continue

            try:
                nb_students = int(nb_students)
            except ValueError:
                self.stderr.write(f"Invalid student count for INSEE code {insee_code}: {nb_students}")
                continue

            city.nb_students += nb_students
            city.save()
            self.stdout.write(f"Updated: {city.name} ({insee_code}) with {city.nb_students} students.")

        self.stdout.write("Update process completed.")
