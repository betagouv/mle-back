import requests
from django.core.management.base import BaseCommand

from territories.models import Academy, Department


class Command(BaseCommand):
    help = "Import departments from public dataset ; currently using https://www.data.gouv.fr/fr/datasets/referentiel-geographique-francais-communes-unites-urbaines-aires-urbaines-departements-academies-regions/#/resources/a1475d8d-e4a4-48a6-8287-f79d21c57904"

    def handle(self, *args, **options):
        url = "https://www.data.gouv.fr/fr/datasets/r/a1475d8d-e4a4-48a6-8287-f79d21c57904"
        self.stdout.write("Downloading GeoJSON file...")

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"Failed to download data: {e}")
            return

        self.stdout.write("Parsing GeoJSON file...")
        data = response.json()

        for line in data:
            dep_code = line["fields"]["dep_code"]
            if Department.objects.filter(code=dep_code).exists():
                continue

            academy = Academy.objects.filter(name__iexact=line["fields"]["aca_nom"]).first()
            if not academy:
                self.stdout.write(f"Unknown academy with name {line['fields']['aca_nom']}. Ignoring the line...")
                continue

            department = Department.objects.create(
                name=line["fields"]["dep_nom"], code=line["fields"]["dep_code"], academy=academy
            )
            self.stdout.write(f"Created {department}")

        self.stdout.write("Departments import completed!")
