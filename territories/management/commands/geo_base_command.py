import json

import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand
from geopy.exc import GeocoderQueryError
from geopy.geocoders import BANFrance

from territories.models import City, Department


class GeoBaseCommand(BaseCommand):
    help = "Base class for Geo commands"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geolocator = BANFrance(timeout=10)

    def _geocode(self, address):
        try:
            return self.geolocator.geocode(address)
        except GeocoderQueryError:
            return None

    def _get_or_create_city(self, city, postal_code):
        # normalize city name
        response = self.fetch_city_from_api(postal_code, city, strict_mode=True)
        if not response:
            return
        city = response["nom"] if response else city
        postal_codes_from_api = response.get("codesPostaux", [])
        if postal_code not in postal_codes_from_api:
            self.stdout.write(self.style.WARNING(f"⚠️ Postal code {postal_code} not found in API for city {city}"))
        city_db = City.objects.filter(name__iexact=city, postal_codes__contains=[postal_code]).first()
        if city_db:
            return city_db

        department_code = postal_code[:2]

        if postal_code.startswith("20"):
            department_code = "2A" if postal_code.startswith("200") or postal_code.startswith("201") else "2B"
        elif postal_code.startswith("97") or postal_code.startswith("98"):
            department_code = postal_code[:3]

        try:
            department_code = Department.objects.get(code=department_code)
        except Department.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Unable to find department {department_code}, cannot create city {city}")
            )
            return
        post_codes = [postal_code] + postal_codes_from_api
        city = City.objects.create(name=city, postal_codes=post_codes, department=department_code)
        return self.fill_city_from_api(city)

    @staticmethod
    def fetch_city_from_api(code, name=None, strict_mode=False):
        base_api_url = "https://geo.api.gouv.fr/communes/"
        returned_fields = "&fields=nom,codesPostaux,codeDepartement,contour,codeEpci,population&format=json"
        filters = ""
        if name:
            filters = f"&nom={name}"

        try:
            response = requests.get(f"{base_api_url}?codePostal={code}{filters}{returned_fields}")
        except requests.exceptions.ConnectTimeout:
            print("GEO API Timeout")
            return

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
