import requests
from django.conf import settings
import certifi
import ssl
from urllib3.poolmanager import PoolManager
from django.contrib.gis.geos import Point

from accommodation.serializers import AccommodationImportSerializer
from territories.management.commands.geo_base_command import GeoBaseCommand
from geopy.geocoders import BANFrance
from geopy.exc import GeocoderUnavailable
from account.models import Owner

class Command(GeoBaseCommand):
    help = "Import iBAIL data"
    root_url = settings.IBAIL_API_HOST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        self.geolocator = BANFrance(
            user_agent='mle-back',
            timeout=10,
            ssl_context=self.ssl_context
        )

    def _get_images_data(self, images):
        images_results = []
        if not images:
            return
        
        for image in images:
            try:
                # First request to get the redirect URL
                initial_response = requests.get(
                    image.get("url"), 
                    verify=certifi.where(),
                    allow_redirects=False  # Don't follow redirects yet
                )
                
                if initial_response.status_code == 302:  # Found redirect
                    final_url = initial_response.headers.get('Location')
                    if final_url:
                        # Now get the actual image from the S3 URL
                        image_response = requests.get(
                            final_url,
                            verify=certifi.where(),
                            allow_redirects=True
                        )
                        
                        if image_response.status_code == 200:
                            images_results.append(image_response.content)
                            self.stdout.write(f"Successfully downloaded image from S3: {final_url}")
                        else:
                            self.stderr.write(f"Failed to download image from S3. Status code: {image_response.status_code}")
                else:
                    self.stderr.write(f"Expected redirect (302) but got status code: {initial_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.stderr.write(f"Error downloading image: {str(e)}")
                continue

        return images_results

    def fetch_data(self):
        headers = {"X-Auth-Key": settings.IBAIL_API_AUTH_KEY, "X-Auth-Secret": settings.IBAIL_API_AUTH_SECRET}
        results = []
        owner = Owner.create({"name": "ARPEJ", "url": "https://www.arpej.fr/fr/"})
        
        current_page = 1
        while True:
            url = f"{self.root_url}/residences?page={current_page}"
            response = requests.get(url, headers=headers, verify=certifi.where())

            if response.status_code != 200:
                self.stderr.write(f"Error retrieving data: {response.json()}")
                break

            residences = response.json()["residences"]
            # Get pagination info from headers
            total_pages = int(response.headers.get("X-Pagination-Total-Pages", 1))
            response_page = int(response.headers.get("X-Pagination-Page", 1))
            total_items = int(response.headers.get("X-Pagination-Total", 0))
            per_page = int(response.headers.get("X-Pagination-Per-Page", 10))
            
            self.stdout.write(f"Processing page {response_page} of {total_pages} (Total items: {total_items})")

            for residence in residences:
                try:
                    full_address = f"{residence.get('address')}, {residence.get('zip_code')} {residence.get('city')}"
                    location = self.geolocator.geocode(full_address)
                    
                    if not location:
                        self.stderr.write(f"Could not geocode address: {full_address}")
                        continue
                        
                    geom = Point(location.longitude, location.latitude, srid=4326)
                    images = self._get_images_data(images=residence.get("pictures"))

                    serializer = AccommodationImportSerializer(
                        data={
                            "name": residence.get("title"),
                            "address": residence.get("address"),
                            "city": residence.get("city"),
                            "postal_code": residence.get("zip_code"),
                            "residence_type": residence.get("residence_type"),
                            "nb_total_apartments": residence.get("availability", {}).get("accommodation_quantity"),
                            "geom": geom,
                            "source_id": residence.get("key"),
                            "images": images,
                            "owner": owner,
                        }
                    )

                    if serializer.is_valid():
                        accommodation = serializer.save()
                        results.append(accommodation)
                        accommodation.save()
                    else:
                        self.stderr.write(f"Error saving residence: {serializer.errors}")
                        continue
                        
                except GeocoderUnavailable as e:
                    self.stderr.write(f"Geocoding error for address {full_address}: {str(e)}")
                    continue
                except Exception as e:
                    self.stderr.write(f"Unexpected error processing residence: {str(e)}")
                    continue

            # Check if we've reached the last page
            if response_page >= total_pages:
                self.stdout.write("Reached the last page")
                break

            # Get the next page number from headers
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