import json

import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand


class GeoBaseCommand(BaseCommand):
    help = "Base class for Geo commands"

    @staticmethod
    def fetch_city_from_api(code):
        base_api_url = "https://geo.api.gouv.fr/communes/"
        returned_fields = "&fields=nom,codesPostaux,codeDepartement,contour,codeEpci,population&format=json"

        response = requests.get(f"{base_api_url}?codePostal={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        # NOTE: this is a dirty workaround, data stored in CLEF is not clean, we can have postal or insee code in same field
        print(f"Cannot found city with postal code {code}, assuming we have an insee code here.")

        response = requests.get(f"{base_api_url}?code={code}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        print(f"Cannot found city with insee code {code}")
        return

    @staticmethod
    def geojson_mpoly(geojson):
        mpoly = GEOSGeometry(geojson if isinstance(geojson, str) else json.dumps(geojson))
        if isinstance(mpoly, MultiPolygon):
            return mpoly
        if isinstance(mpoly, Polygon):
            return MultiPolygon([mpoly])
        raise TypeError(f"{mpoly.geom_type} not acceptable for this model")
