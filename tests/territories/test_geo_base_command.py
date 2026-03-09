import pytest
from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from territories.management.commands.geo_base_command import GeoBaseCommand

pytestmark = pytest.mark.django_db


def test_geocode_retries_then_succeeds(monkeypatch):
    command = GeoBaseCommand()
    monkeypatch.setattr("territories.management.commands.geo_base_command.sleep", lambda *_: None)

    attempts = {"count": 0}

    class StubGeolocator:
        def geocode(self, _address):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise GeocoderTimedOut("504 timeout")
            return {"ok": True}

    command.geolocator = StubGeolocator()

    assert command._geocode("10 rue de la paix") == {"ok": True}
    assert attempts["count"] == 3


def test_geocode_returns_none_after_retries(monkeypatch):
    command = GeoBaseCommand()
    monkeypatch.setattr("territories.management.commands.geo_base_command.sleep", lambda *_: None)

    class StubGeolocator:
        def geocode(self, _address):
            raise GeocoderServiceError("service unavailable")

    command.geolocator = StubGeolocator()

    assert command._geocode("10 rue de la paix", retries=2) is None
