import requests
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management.base import BaseCommand

from territories.models import Academy


class Command(BaseCommand):
    help = "Import academies from public dataset ; currently using https://www.data.gouv.fr/fr/datasets/contour-academies-2020/#/resources -> https://www.data.gouv.fr/fr/datasets/contour-academies-2020/#/resources/46417429-430c-4886-9a0d-6dd3a040391a"

    def handle(self, *args, **options):
        url = "https://www.data.gouv.fr/fr/datasets/r/46417429-430c-4886-9a0d-6dd3a040391a"
        self.stdout.write("Downloading GeoJSON file...")

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"Failed to download data: {e}")
            return

        self.stdout.write("Parsing GeoJSON file...")
        data = response.json()

        self.stdout.write("Importing academies into the database...")
        for academy_json in data:
            academy_name = academy_json.get("name", "").strip().capitalize()

            if not academy_name:
                self.stderr.write("Skipping entry with empty name")
                continue

            academy, created = Academy.objects.update_or_create(name=academy_name)
            geo_shape = academy_json.get("geo_shape")
            multipolygon = None
            if geo_shape:
                geometry_type = geo_shape["geometry"]["type"]

                if geometry_type == "Polygon":
                    polygon = Polygon(geo_shape["geometry"]["coordinates"][0])
                    multipolygon = MultiPolygon(polygon)
                elif geometry_type == "MultiPolygon":
                    multipolygon = MultiPolygon(
                        *[Polygon(coords[0]) for coords in geo_shape["geometry"]["coordinates"]]
                    )
                else:
                    print(f"Unsupported geometry type: {geometry_type}. Ignoring...")

            academy.boundary = multipolygon

            academy.save()

            if created:
                self.stdout.write(f"Added new academy: {academy_name}")
            else:
                self.stdout.write(f"Updated existing academy: {academy_name}")

        self.stdout.write("Academies import completed!")
