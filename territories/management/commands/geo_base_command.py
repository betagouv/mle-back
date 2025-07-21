import json

import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand


class GeoBaseCommand(BaseCommand):
    help = "Base class for Geo commands"

    @staticmethod
    def fetch_city_from_api(code, name=None, strict_mode=False):
        base_api_url = "https://geo.api.gouv.fr/communes/"
        returned_fields = "&fields=nom,codesPostaux,codeDepartement,contour,codeEpci,population&format=json"
        filters = ""
        if name:
            filters = f"&nom={name}"

        response = requests.get(f"{base_api_url}?codePostal={code}{filters}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        if strict_mode:
            return

        # NOTE: this is a dirty workaround, data stored in CLEF is not clean, we can have postal or insee code in same field
        print(f"Cannot found city with postal code {code}, assuming we have an insee code here.")

        response = requests.get(f"{base_api_url}?code={code}{filters}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        print(f"Cannot found city with insee code {code}")
        return

    def fill_city_from_api(self, city):
        response = self.fetch_city_from_api(city.postal_codes[0], city.name)
        if response:
            city.name = response["nom"]
            city.boundary = self.geojson_mpoly(response["contour"])
            city.epci_code = response.get("codeEpci")
            city.population = response.get("population", 0)
            city.insee_codes = list(set(city.insee_codes + [response["code"]]))
            city.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✔️ {city.name} created/updated with INSEE {city.insee_codes}, boundary, epci_code and population"
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Unable to fetch detailed info for {city.name}"))
        return city

    @staticmethod
    def geojson_mpoly(geojson):
        mpoly = GEOSGeometry(geojson if isinstance(geojson, str) else json.dumps(geojson))
        if isinstance(mpoly, MultiPolygon):
            return mpoly
        if isinstance(mpoly, Polygon):
            return MultiPolygon([mpoly])
        raise TypeError(f"{mpoly.geom_type} not acceptable for this model")
