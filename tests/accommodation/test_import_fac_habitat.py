import json
from io import StringIO

import pytest
from django.core.management import call_command

from accommodation.models import Accommodation, ExternalSource
from accommodation.management.commands.import_fac_habitat import Command


@pytest.mark.django_db
def test_import_fac_habitat_uses_external_reference_for_idempotence(tmp_path):
    initial_payload = [
        {
            "id": "10771003",
            "marque": "FACH",
            "name": "Abelard",
            "address": "53 Rue Louis Charles Vernin",
            "city": "Melun",
            "postal_code": "77000",
            "accept_waiting_list": False,
            "laundry_room": True,
            "parking": True,
            "residence_manager": True,
            "kitchen_type": "private",
            "refrigerator": True,
            "bathroom": "private",
            "nb_accessible_apartments": 3,
            "nb_coliving_apartments": 1,
            "nb_total_apartments": 85,
            "nb_t1": 84,
            "t1_rent_min": 453.77,
            "t1_rent_max": 518.44,
            "nb_t1_bis": 1,
            "t1_bis_rent_min": 600.0,
            "t1_bis_rent_max": 650.0,
            "nb_t1_prime": 2,
            "t1_prime_rent_min": 550.0,
            "t1_prime_rent_max": 700.0,
            "nb_studio_double": 3,
            "studio_double_rent_min": 580.0,
            "studio_double_rent_max": 720.0,
            "nb_t2": 4,
            "t2_rent_min": 800.0,
            "t2_rent_max": 900.0,
            "nb_t2_duplex": 1,
            "t2_duplex_rent_min": 950.0,
            "t2_duplex_rent_max": 1000.0,
            "nb_duplex": 2,
            "duplex_rent_min": 910.0,
            "duplex_rent_max": 980.0,
            "nb_t3": 1,
            "t3_rent_min": 1100.0,
            "t3_rent_max": 1200.0,
            "nb_duo": 2,
            "duo_rent_min": 1050.0,
            "duo_rent_max": 1250.0,
            "nb_t4": 1,
            "t4_rent_min": 1300.0,
            "t4_rent_max": 1400.0,
            "nb_t5_en_colocation": 1,
            "t5_en_colocation_rent_min": 1500.0,
            "t5_en_colocation_rent_max": 1600.0,
        }
    ]

    json_file = tmp_path / "fac_habitat.json"
    json_file.write_text(json.dumps(initial_payload), encoding="utf-8")

    call_command("import_fac_habitat", file=str(json_file))

    accommodation = Accommodation.objects.get(external_reference="10771003")

    assert accommodation.owner.name == "FAC HABITAT"
    assert accommodation.nb_t1 == 84
    assert accommodation.nb_t1_bis == 6
    assert accommodation.price_min_t1_bis == 550
    assert accommodation.price_max_t1_bis == 720
    assert accommodation.nb_t2 == 7
    assert accommodation.price_min_t2 == 800
    assert accommodation.price_max_t2 == 1000
    assert accommodation.nb_t3 == 3
    assert accommodation.price_min_t3 == 1050
    assert accommodation.price_max_t3 == 1250
    assert accommodation.nb_t5 == 1
    assert accommodation.nb_total_apartments == 102
    assert accommodation.sources.filter(
        source=ExternalSource.SOURCE_FAC_HABITAT,
        source_id="10771003",
    ).exists()

    updated_payload = [dict(initial_payload[0], name="Abelard Updated", parking=False, nb_t1=80)]
    json_file.write_text(json.dumps(updated_payload), encoding="utf-8")

    call_command("import_fac_habitat", file=str(json_file))

    accommodation.refresh_from_db()

    assert Accommodation.objects.count() == 1
    assert accommodation.name == "Abelard Updated"
    assert accommodation.parking is False
    assert accommodation.nb_t1 == 80


@pytest.mark.django_db
def test_import_fac_habitat_uses_injected_sftp_downloader(tmp_path):
    downloaded_file = tmp_path / "downloaded.json"
    downloaded_file.write_text("[]", encoding="utf-8")
    calls = {}

    class StubDownloader:
        def download(self, remote_path):
            calls["remote_path"] = remote_path
            return downloaded_file

    def stub_factory(*, stdout, mode, fixture_file):
        calls["mode"] = mode
        calls["fixture_file"] = fixture_file
        return StubDownloader()

    command = Command(sftp_downloader_factory=stub_factory)
    command.stdout = StringIO()
    command.handle(
        file=None,
        sftp_mode="fake",
        fixture_file="~/Downloads/fac_habitat.json",
        remote_path="/remote/fac_habitat.json",
    )

    assert calls == {
        "mode": "fake",
        "fixture_file": "~/Downloads/fac_habitat.json",
        "remote_path": "/remote/fac_habitat.json",
    }
