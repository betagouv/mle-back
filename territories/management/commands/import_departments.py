import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand

from territories.models import Academy, Department


class Command(BaseCommand):
    help = "Import departments from public dataset and populate boundaries using GeoJSON data"

    def handle(self, *args, **options):
        departments_url = "https://www.data.gouv.fr/fr/datasets/r/a1475d8d-e4a4-48a6-8287-f79d21c57904"
        boundaries_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"

        self.stdout.write("Downloading departments dataset...")
        try:
            dep_response = requests.get(departments_url)
            dep_response.raise_for_status()
            departments_data = dep_response.json()
        except requests.RequestException as e:
            self.stderr.write(f"Failed to download departments dataset: {e}")
            return

        self.stdout.write("Downloading boundaries GeoJSON dataset...")
        try:
            boundaries_response = requests.get(boundaries_url)
            boundaries_response.raise_for_status()
            boundaries_data = boundaries_response.json()
        except requests.RequestException as e:
            self.stderr.write(f"Failed to download boundaries dataset: {e}")
            return

        self.stdout.write("Processing boundaries dataset...")
        boundaries_lookup = {}
        for feature in boundaries_data["features"]:
            dep_code = feature["properties"]["code"]
            geometry = feature["geometry"]

            geo = GEOSGeometry(str(geometry))

            if isinstance(geo, Polygon):
                geo = MultiPolygon(geo)

            boundaries_lookup[dep_code] = geo

        self.stdout.write("Processing departments dataset...")
        managed_departments = []
        for line in departments_data:
            dep_code = line["fields"]["dep_code"]
            if dep_code in managed_departments:
                continue

            academy = Academy.objects.filter(name__iexact=line["fields"]["aca_nom"]).first()
            if not academy:
                self.stdout.write(f"Unknown academy with name {line['fields']['aca_nom']}. Ignoring the line...")
                continue

            department, _ = Department.objects.get_or_create(code=dep_code, academy=academy)

            department.name = line["fields"]["dep_nom"]
            boundary = boundaries_lookup.get(dep_code)
            if boundary:
                department.boundary = boundary
                department.save()
                self.stdout.write(f"Updated boundary for department {department.name} ({dep_code})")
            else:
                self.stdout.write(f"No boundary found for department {department.name} ({dep_code})")
            managed_departments.append(dep_code)

        self.stdout.write("Departments import completed!")
