import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import BANFrance

from accommodation.models import ExternalSource
from accommodation.serializers import AccommodationImportSerializer
from account.models import Owner
from territories.management.commands.geo_base_command import GeoBaseCommand


class Command(GeoBaseCommand):
    help = "Import iBAIL (arpej) data"
    root_url = settings.IBAIL_API_HOST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geolocator = BANFrance(timeout=10)

    def _get_images_data(self, images):
        images_results = []
        if not images:
            return

        for image in images:
            try:
                initial_response = requests.get(image.get("url"), allow_redirects=False)

                if initial_response.status_code != 302:
                    self.stderr.write(f"Expected redirect (302) but got status code: {initial_response.status_code}")
                    continue

                if final_url := initial_response.headers.get("Location"):
                    image_response = requests.get(final_url, allow_redirects=True)

                    if image_response.status_code == 200:
                        images_results.append(image_response.content)
                        self.stdout.write(f"Successfully downloaded image from S3: {final_url}")
                    else:
                        self.stderr.write(
                            f"Failed to download image from S3. Status code: {image_response.status_code}"
                        )

            except requests.exceptions.RequestException as e:
                self.stderr.write(f"Error downloading image: {str(e)}")
                continue

        return images_results

    def fetch_data(self):
        headers = {"X-Auth-Key": settings.IBAIL_API_AUTH_KEY, "X-Auth-Secret": settings.IBAIL_API_AUTH_SECRET}
        results = []
        owner = Owner.get_or_create({"name": "ARPEJ", "url": "https://www.arpej.fr/fr/"})

        def to_digit(value):
            if not value:
                return
            if isinstance(value, str):
                value = value.replace("€", "").strip()
            return int(value)

        current_page = 1
        while True:
            url = f"{self.root_url}/residences?page={current_page}"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                self.stderr.write(f"Error retrieving data: {response.json()}")
                break

            residences = response.json()["residences"]
            total_pages = int(response.headers.get("X-Pagination-Total-Pages", 1))
            response_page = int(response.headers.get("X-Pagination-Page", 1))
            total_items = int(response.headers.get("X-Pagination-Total", 0))

            self.stdout.write(f"Processing page {response_page} of {total_pages} (Total items: {total_items})")

            for residence in residences:
                try:
                    full_address = f"{residence.get('address')} {residence.get('address_completement')}, {residence.get('zip_code')} {residence.get('city')}"
                    location = self.geolocator.geocode(full_address)

                    if not location:
                        self.stderr.write(f"Could not geocode address: {full_address}")
                        continue

                    geom = Point(location.longitude, location.latitude, srid=4326)
                    images = self._get_images_data(images=residence.get("pictures"))

                    city = location.raw["properties"]["city"]
                    address = location.raw["properties"]["name"]
                    postal_code = location.raw["properties"]["postcode"]

                    serializer = AccommodationImportSerializer(
                        data={
                            "name": residence.get("title"),
                            "address": address,
                            "residence_type": "universitaire-conventionnee",
                            "city": city,
                            "postal_code": postal_code,
                            "price_min_t1": to_digit(residence.get("availability", {}).get("rent_amount_from")),
                            "nb_total_apartments": residence.get("availability", {}).get("accommodation_quantity"),
                            "geom": geom,
                            "source": ExternalSource.SOURCE_ARPEJ,
                            "source_id": residence.get("key"),
                            "images": images,
                            "owner_id": owner.pk if owner else None,
                        }
                    )

                    if serializer.is_valid():
                        accommodation = serializer.save()
                        self.stdout.write(f"Successfully inserted {accommodation.name} - {full_address}")
                        results.append(accommodation)
                    else:
                        self.stderr.write(f"Error saving residence: {serializer.errors}")
                        continue

                except GeocoderUnavailable as e:
                    self.stderr.write(f"Geocoding error for address {full_address}: {str(e)}")
                    continue
                except Exception as e:
                    self.stderr.write(f"Unexpected error processing residence: {str(e)}")
                    continue

            if response_page >= total_pages:
                self.stdout.write("Reached the last page")
                break

            next_page = response.headers.get("X-Pagination-Next-Page")
            if not next_page:
                self.stdout.write("No next page available")
                break

            current_page = int(next_page)
            self.stdout.write(f"Moving to next page: {current_page}")

        return results

    def handle(self, *args, **options):
        self.stdout.write("Starting iBAIL import via IBAIL API...")

        data = self.fetch_data()
        if not data:
            self.stderr.write("No data retrieved. Aborting.")
            return

        self.stdout.write(f"Import completed with {len(data)} records.")
