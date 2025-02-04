import requests
from django.conf import settings

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
        response = requests.get(..., headers=headers)

        if response.status_code != 200:
            self.stderr.write(f"Error retrieving data: {response.json()}")
            return

        return response.json()

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
