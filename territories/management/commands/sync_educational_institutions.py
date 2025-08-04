import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from geopy.adapters import AdapterHTTPError
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import BANFrance

from territories.management.commands.geo_base_command import GeoBaseCommand
from territories.models import EducationalInstitution


class Command(GeoBaseCommand):
    help = "Import educational institutions from OMOGEN API"

    root_url = f"https://{settings.OMOGEN_API_HOST}"
    auth_url = f"{root_url}/{settings.OMOGEN_API_AUTH_PATH}"
    access_token = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geolocator = BANFrance(timeout=10)

    def refresh_access_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.OMOGEN_API_CLIENT_ID,
            "client_secret": settings.OMOGEN_API_CLIENT_SECRET,
        }
        headers = {
            "X-omogen-api-key": settings.OMOGEN_API_API_KEY,
            "Content-type": "application/x-www-form-urlencoded",
        }

        response = requests.post(self.auth_url, data=payload, headers=headers)
        if response.status_code != 200:
            self.stderr.write(f"Error retrieving token: {response.text}")
            return

        self.stdout.write("Successfully retrieved token")
        self.access_token = response.json().get("access_token")

    def do_request(self, url):
        if not self.access_token:
            self.refresh_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-omogen-api-key": settings.OMOGEN_API_API_KEY,
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            self.stderr.write("Token expired, refreshing...")
            self.refresh_access_token()
            return self.do_request(url)

        if response.status_code != 200:
            self.stderr.write(f"Error fetching data ({response.status_code}): {response.text}")
            return None

        return response.json()

    def fetch_data(self, page=1):
        url = f"{self.root_url}/{settings.OMOGEN_API_RAMSESE_APP_NAME}/v3?page={page}"
        self.stdout.write(f"Fetching institutions - page {page} - {url}")
        data = self.do_request(url)

        if not data:
            return []

        institutions = data.get("content", [])
        saved = []

        for inst in institutions:
            name = inst.get("nom")
            address = inst.get("adresse")
            city = inst.get("ville")
            postal_code = inst.get("codePostal")
            website = inst.get("siteWeb")

            try:
                location = self.geolocator.geocode(f"{address}, {postal_code} {city}")
            except (AdapterHTTPError, GeocoderTimedOut):
                location = None

            if not location:
                self.stderr.write(f"Could not geocode: {address}, {postal_code} {city}")
                continue

            geom = Point(location.longitude, location.latitude, srid=4326)

            institution, created = EducationalInstitution.objects.update_or_create(
                source_id=inst.get("id"),
                defaults={
                    "name": name,
                    "address": address,
                    "postal_code": postal_code,
                    "city": city,
                    "website": website,
                    "geom": geom,
                    "source": "omogen",
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {institution.name}"))
            else:
                self.stdout.write(f"Updated: {institution.name}")

            saved.append(institution)

        if not data.get("last"):
            saved += self.fetch_data(page + 1)

        return saved

    def handle(self, *args, **options):
        self.stdout.write("Starting OMOGEN educational institutions sync...")
        institutions = self.fetch_data()
        self.stdout.write(self.style.SUCCESS(f"Imported {len(institutions)} institutions"))
