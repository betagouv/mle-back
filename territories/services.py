import logging
import requests
import sib_api_v3_sdk
import json
from django.conf import settings

from typing import Protocol

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon

from territories.models import Academy, City, Department

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = settings.BREVO_API_KEY
api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))

logger = logging.getLogger(__name__)


def sync_newsletter_subscription_to_brevo(email, territory_type, territory_name, kind):
    contact_data = {
        "attributes": {"TERRITORY_NAME": territory_name, "TERRITORY_TYPE": territory_type, "KIND": kind},
        "listIds": [settings.BREVO_CONTACT_LIST_ID],
        "updateEnabled": True,
    }
    try:
        api_instance.get_contact_info(email)
        api_instance.update_contact(email, contact_data)
    except sib_api_v3_sdk.rest.ApiException as e:
        if e.status == 404:
            contact_data["email"] = email
            api_instance.create_contact(contact_data)


class CityManagerServiceProtocol(Protocol):
    def get_or_create_city(self, city, postal_code) -> City: ...


class CityManagerService:
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
            logger.error("GEO API Timeout")
            return

        if response_json := response.json():
            return response_json[0]

        if strict_mode:
            return

        # NOTE: this is a dirty workaround, data stored in CLEF is not clean, we can have postal or insee code in same field
        logger.error(f"Cannot found city with postal code {code}, assuming we have an insee code here.")

        response = requests.get(f"{base_api_url}?code={code}{filters}{returned_fields}")
        if response_json := response.json():
            return response_json[0]

        logger.error(f"Cannot found city with insee code {code}")
        return

    def get_or_create_city(self, city, postal_code):
        # normalize city name
        response = self.fetch_city_from_api(postal_code, city, strict_mode=True)
        if not response:
            return
        city = response["nom"] if response else city
        postal_codes_from_api = response.get("codesPostaux", [])
        if postal_code not in postal_codes_from_api:
            logger.warning(f"⚠️ Postal code {postal_code} not found in API for city {city}")
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
            logger.warning(f"Unable to find department {department_code}, cannot create city {city}")
            return
        post_codes = [postal_code] + postal_codes_from_api
        city = City.objects.create(name=city, postal_codes=post_codes, department=department_code)
        return self.fill_city_from_api(city)

    def fill_city_from_api(self, city):
        response = self.fetch_city_from_api(city.postal_codes[0], city.name)
        if response:
            city.name = response["nom"]
            city.boundary = self.geojson_mpoly(response["contour"])
            city.epci_code = response.get("codeEpci")
            city.population = response.get("population", 0)
            city.insee_codes = list(set(city.insee_codes + [response["code"]]))
            city.save()
            logger.info(
                f"{city.name} created/updated with INSEE {city.insee_codes}, boundary, epci_code and population"
            )
        else:
            logger.warning(f"Unable to fetch detailed info for {city.name}")
        return city

    @staticmethod
    def geojson_mpoly(geojson):
        mpoly = GEOSGeometry(geojson if isinstance(geojson, str) else json.dumps(geojson))
        if isinstance(mpoly, MultiPolygon):
            return mpoly
        if isinstance(mpoly, Polygon):
            return MultiPolygon([mpoly])
        raise TypeError(f"{mpoly.geom_type} not acceptable for this model")


class FakeCityManagerService:
    def get_or_create_city(self, city, postal_code) -> City:
        academy, _ = Academy.objects.get_or_create(name="Academy 1")
        department, _ = Department.objects.get_or_create(name="Department 1", academy=academy)
        city, _ = City.objects.get_or_create(name=city, postal_codes=[postal_code], department=department)
        return city


def get_city_manager_service() -> CityManagerServiceProtocol:
    return CityManagerService()
