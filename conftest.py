import os
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from django.db import connection


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


def mock_requests_get(url, *args, **kwargs):
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)

    if parsed_url.netloc == "geo.api.gouv.fr":
        postal_code = params.get("codePostal", [None])[0]
        city = params.get("nom", [None])[0]

        mock_response = mock.Mock()
        mock_response.json.return_value = [
            {
                "nom": city,
                "codesPostaux": [postal_code],
                "codeDepartement": f"{postal_code[0:2]}",
                "contour": "POLYGON((2.3522 48.8566, 2.3523 48.8567, 2.3524 48.8568, 2.3525 48.8567, 2.3522 48.8566))",
            }
        ]
        return mock_response

    return requests.get(url, *args, **kwargs)


@pytest.fixture(autouse=True)
def mock_get_requests():
    with mock.patch("requests.get", side_effect=mock_requests_get):
        yield
