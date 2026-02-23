import os
import re
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import faker
import pytest
import requests_mock
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection

from accommodation.models import Accommodation

from territories.services import FakeCityManagerService

fake = faker.Faker()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    assert os.environ.get("DJANGO_SETTINGS_MODULE") == "config.settings.test"

    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
        cursor.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS french_unaccent cascade")
        cursor.execute("CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french )")
        cursor.execute(
            "ALTER TEXT SEARCH CONFIGURATION french_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem"
        )


@pytest.fixture(autouse=True)
def mock_requests():
    with requests_mock.Mocker() as mocker:

        def geo_api_mock(request, context):
            parsed_url = urlparse(request.url)
            params = parse_qs(parsed_url.query)
            postal_code = params.get("codePostal", [None])[0]

            return [
                {
                    "nom": fake.city(),
                    "codesPostaux": [postal_code],
                    "code": f"{postal_code}",
                    "codeDepartement": f"{postal_code[:2]}",
                    "contour": "POLYGON((2.3522 48.8566, 2.3523 48.8567, 2.3524 48.8568, 2.3525 48.8567, 2.3522 48.8566))",
                    "codeEpci": "123456789",
                }
            ]

        mocker.get("https://geo.api.gouv.fr/communes/", json=geo_api_mock)
        mocker.get(re.compile(r"https://image\.com/.*"), content=b"fake image", status_code=200)

        yield mocker


@pytest.fixture(autouse=True)
def mock_geolocator():
    with patch("accommodation.serializers.get_geolocator") as mock_get_geolocator:
        mock_geolocator_instance = MagicMock()
        mock_geolocator_instance.geocode.return_value = MagicMock(
            latitude=48.85,
            longitude=2.35,
        )
        mock_get_geolocator.return_value = mock_geolocator_instance
        yield mock_get_geolocator


@pytest.fixture(autouse=True)
def mock_city_manager_service():
    with patch("accommodation.serializers.get_city_manager_service") as mock_get_city_manager_service:
        mock_get_city_manager_service.return_value = FakeCityManagerService()
        yield mock_get_city_manager_service


@pytest.fixture(autouse=True)
def create_owners_group():
    owners_group, _ = Group.objects.get_or_create(name="Owners")

    content_type = ContentType.objects.get_for_model(Accommodation)

    can_view_accommodation = Permission.objects.get(
        codename="view_accommodation",
        content_type=content_type,
    )
    can_change_accommodation = Permission.objects.get(
        codename="change_accommodation",
        content_type=content_type,
    )

    owners_group.permissions.set([can_view_accommodation, can_change_accommodation])

    return owners_group
