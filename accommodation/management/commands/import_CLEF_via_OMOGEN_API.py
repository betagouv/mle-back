import requests
from django.conf import settings
from django.contrib.gis.geos import Point

from accommodation.serializers import AccommodationImportSerializer
from territories.management.commands.geo_base_command import GeoBaseCommand


class Command(GeoBaseCommand):
    help = "Import CLEF data via OMOGEN API"

    def get_access_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.OMOGEN_API_CLIENT_ID,
            "client_secret": settings.OMOGEN_API_CLIENT_SECRET,
        }
        headers = {"X-omogen-api-key": settings.OMOGEN_API_API_KEY, "Content-type": "application/x-www-form-urlencoded"}

        response = requests.post(f"https://{settings.OMOGEN_API_HOST}/auth-test/token", data=payload, headers=headers)
        response_data = response.json()

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving token: {response_data}")
            return

        return response_data.get("access_token")

    def fetch_data(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}", "X-omogen-api-key": settings.OMOGEN_API_API_KEY}

        url = f"https://{settings.OMOGEN_API_HOST}/v1/external/getResidences"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving data: {response.json()}")
            return

        residences = response.json()

        for residence in residences:
            images = []
            image_ids = residence.get("imageIds", [])

            for image_id in image_ids:
                image_url = f"https://{settings.OMOGEN_API_HOST}/v1/images/{image_id}"
                image_response = requests.get(image_url, headers=headers)

                if image_response.status_code == 200:
                    images.append(image_response.content)
                else:
                    self.stderr.write(f"Error retrieving image {image_id}: {image_response.status_code}")

            serializer = AccommodationImportSerializer(
                data={
                    "name": ...,
                    "address": ...,
                    "city": ...,
                    "postal_code": ...,
                    "residence_type": ...,
                    "owner_name": ...,
                    "owner_url": ...,
                    "nb_total_apartments": ...,
                    "nb_accessible_apartments": ...,
                    "nb_coliving_apartments": ...,
                    "nb_t1": ...,
                    "nb_t1_bis": ...,
                    "nb_t2": ...,
                    "nb_t3": ...,
                    "nb_t4_more": ...,
                    "geom": Point(residence["longitude"], residence["latitude"])
                    if "longitude" in residence and "latitude" in residence
                    else None,
                    "source_id": residence.get("id"),
                    "images": images,
                }
            )

            if serializer.is_valid():
                serializer.save()
            else:
                self.stderr.write(f"Error saving residence: {serializer.errors}")
                continue

        return residences

    def handle(self, *args, **options):
        self.stdout.write("Starting CLEF import via OMOGEN API...")

        access_token = self.get_access_token()
        if not access_token:
            self.stderr.write("Failed to obtain access token. Aborting.")
            return

        data = self.fetch_data(access_token)
        if not data:
            self.stderr.write("No data retrieved. Aborting.")
            return

        self.stdout.write(f"Import completed with {len(data)} records.")
