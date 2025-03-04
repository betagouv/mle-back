import requests
from django.conf import settings
from django.contrib.gis.geos import Point

from accommodation.serializers import AccommodationImportSerializer
from territories.management.commands.geo_base_command import GeoBaseCommand
from account.models import Owner


class Command(GeoBaseCommand):
    help = "Import CLEF data via OMOGEN API"
    root_url = f"https://{settings.OMOGEN_API_HOST}"

    def get_access_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.OMOGEN_API_CLIENT_ID,
            "client_secret": settings.OMOGEN_API_CLIENT_SECRET,
        }
        headers = {"X-omogen-api-key": settings.OMOGEN_API_API_KEY, "Content-type": "application/x-www-form-urlencoded"}

        response = requests.post(f"{self.root_url}/auth-test/token", data=payload, headers=headers)
        response_data = response.json()

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving token: {response_data}")
            return

        self.stdout.write("Successfully retrieved token")
        return response_data.get("access_token")

    def _get_owner_data(self, owner_id, access_token):
        if not owner_id:
            return

        headers = {"Authorization": f"Bearer {access_token}", "X-omogen-api-key": settings.OMOGEN_API_API_KEY}
        url = f"{self.root_url}/v1/type-gestionnaires/{owner_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return

        owner_data = response.json()
        return {"name": owner_data.get(...), "url": owner_data.get(...)}

    def _get_images_data(self, image_ids, access_token):
        if not image_ids:
            return

        headers = {"Authorization": f"Bearer {access_token}", "X-omogen-api-key": settings.OMOGEN_API_API_KEY}
        images = []

        for image_id in image_ids:
            image_url = f"{self.root_url}/v1/images/{image_id}"
            image_response = requests.get(image_url, headers=headers)

            if image_response.status_code == 200:
                images.append(image_response.content)
            else:
                self.stderr.write(f"Error retrieving image {image_id}: {image_response.status_code}")

        return images

    def fetch_data(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}", "X-omogen-api-key": settings.OMOGEN_API_API_KEY}

        url = f"{self.root_url}/v1/external/getResidences"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving data: {response.json()}")
            return

        residences = response.json()
        results = []

        for residence in residences:
            images = self._get_images_data(image_ids=residence.get("imageIds"), access_token=access_token)
            owner_data = self._get_owner_data(residence.get("typeGestionnaireId"), access_token=access_token)

            serializer = AccommodationImportSerializer(
                data={
                    "name": ...,
                    "address": ...,
                    "city": ...,
                    "postal_code": ...,
                    "residence_type": ...,
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
                    "owner_id": residence.get("typeGestionnaireId"),
                    "images": images,
                }
            )

            if serializer.is_valid():
                accommodation = serializer.save()
                results.append(accommodation)

                owner = Owner.create(owner_data)
                accommodation.owner = owner
                accommodation.save()
            else:
                self.stderr.write(f"Error saving residence: {serializer.errors}")
                continue

        return results

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
