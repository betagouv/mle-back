import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from geopy.adapters import AdapterHTTPError
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import BANFrance

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner
from territories.management.commands.geo_base_command import GeoBaseCommand

owners_to_ignore = [
    "studefi",
    "efidis studefi",
    "arpej",
    "agefo",
    "s.a. espacil habitat",
    "sa hlm espacil habitat",
    "esh espacil habitat",
    "sa hlm espacil habitat",
    "espacil",
    "espacil habitat",
]


class Command(GeoBaseCommand):
    help = "Import CLEF data via OMOGEN API"
    root_url = f"https://{settings.OMOGEN_API_HOST}"
    auth_url = f"{root_url}/{settings.OMOGEN_API_AUTH_PATH}"
    access_token = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geolocator = BANFrance(timeout=10)

    def do_request(self, url):
        if not self.access_token:
            self.refresh_access_token()

        headers = {"Authorization": f"Bearer {self.access_token}", "X-omogen-api-key": settings.OMOGEN_API_API_KEY}
        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            self.stderr.write(f"Unauthorized error retrieving data from url {url}: refreshing token")
            self.refresh_access_token()
            return self.do_request(url)

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving data from url {url} (HTTP {response.status_code}): {response.content}")
            return

        return response

    def refresh_access_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.OMOGEN_API_CLIENT_ID,
            "client_secret": settings.OMOGEN_API_CLIENT_SECRET,
        }
        headers = {"X-omogen-api-key": settings.OMOGEN_API_API_KEY, "Content-type": "application/x-www-form-urlencoded"}

        response = requests.post(self.auth_url, data=payload, headers=headers)
        response_data = response.json()

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving token: {response_data}")
            return

        self.stdout.write("Successfully retrieved token")
        self.access_token = response_data.get("access_token")

    def _get_images_data(self, image_ids):
        if not image_ids:
            return

        images = []

        for image_id in image_ids:
            image_url = f"{self.root_url}/{settings.OMOGEN_API_CLEF_APP_NAME}/v1/images/{image_id}"
            image_response = self.do_request(image_url)

            if image_response.status_code == 200:
                images.append(image_response.content)
            else:
                self.stderr.write(f"Error retrieving image {image_id}: {image_response.status_code}")

        return images

    def fetch_data(self, page=1):
        self.stdout.write(f"Fetching page {page}")
        url = f"{self.root_url}/{settings.OMOGEN_API_CLEF_APP_NAME}/v1/external/getResidences?page={page}"

        response = self.do_request(url)

        if not response:
            return []

        response = response.json()
        residences = response.get("content", [])
        results = []

        for residence in residences:
            images = self._get_images_data(image_ids=residence.get("images"))

            residence_id = residence.get("idTypeResidence")
            if residence_id != 2:
                self.stdout.write(self.style.NOTICE(f"Skipping accommodation with id {residence_id}"))
                continue

            status_id = residence.get("idStatutResidence")
            if status_id != 3:
                self.stdout.write(self.style.NOTICE(f"Skipping accommodation with status {status_id}"))
                continue

            if (name := residence.get("nom")).startswith("Residence TMC"):
                self.stdout.write(self.style.NOTICE(f"Skipping TMC accommodation {name}, created for tests."))
                continue

            try:
                location = self.geolocator.geocode(residence.get("adresseGeolocalisee"))
            except (AdapterHTTPError, GeocoderTimedOut):
                location = None

            if not location:
                self.stderr.write(f"Could not geocode address: {residence.get('adresseGeolocalisee')}")
                continue

            geom = Point(location.longitude, location.latitude, srid=4326)

            city = location.raw["properties"]["city"]
            address = location.raw["properties"]["name"]
            postal_code = location.raw["properties"]["postcode"]

            owner = None
            if owner_name := residence.get("gestionnaireNom"):
                if owner_name.lower() in owners_to_ignore:
                    self.stdout.write(self.style.NOTICE(f"Skipping owner {owner_name}"))
                    continue
                owner_data = {"name": owner_name, "url": residence.get("gestionnaireSite")}
                owner = Owner.get_or_create(owner_data)

            serializer = AccommodationImportSerializer(
                data={
                    "name": name,
                    "address": address,
                    "city": city,
                    "postal_code": postal_code,
                    "residence_type": "universitaire-conventionnee",
                    "nb_total_apartments": residence.get("nombreTotalLogement"),
                    "nb_accessible_apartments": residence.get("nombreLogementPMR"),
                    "nb_coliving_apartments": residence.get("nombreTotalPlaceCollocation"),
                    "nb_t1": residence.get("nombreT1"),
                    "nb_t1_bis": residence.get("nombreT1Bis"),
                    "nb_t2": residence.get("nombreT2"),
                    "nb_t3": residence.get("nombreT3"),
                    "nb_t4_more": residence.get("nombreT4Plus"),
                    "geom": geom,
                    "source": ExternalSource.SOURCE_CLEF,
                    "source_id": residence.get("id"),
                    "images_content": images or [],
                    "published": True,
                    "owner_id": owner.pk if owner else None,
                }
            )

            if serializer.is_valid():
                accommodation = serializer.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully inserted {accommodation.name} - {residence.get('adresseGeolocalisee')}"
                    )
                )
                results.append(accommodation)
            else:
                self.stderr.write(f"Error saving accommodation: {serializer.errors}")
                continue

        if not response.get("last"):
            results.extend(self.fetch_data(page=page + 1))

        return results

    def handle(self, *args, **options):
        self.stdout.write("Starting CLEF import via OMOGEN API...")

        data = self.fetch_data()
        if not data:
            self.stderr.write("No data retrieved. Aborting.")
            return

        self.stdout.write(f"Import completed with {len(data)} accommodations.")
