from unittest import mock

import pytest
import requests_mock
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management import call_command

from accommodation.models import Accommodation, ExternalSource, Owner
from tests.territories.factories import AcademyFactory, DepartmentFactory


@pytest.mark.django_db
def test_residence_type_mapping():
    academy = AcademyFactory(name="France")

    DepartmentFactory(code="75", academy=academy)
    DepartmentFactory(code="13", academy=academy)
    DepartmentFactory(code="69", academy=academy)

    csv_data = """Identifiant fonctionnel,Nom de la résidence,Type de résidence,Adresse administrative,Commune,Code postal,Latitude,Longitude,Gestionnaire - Nom,Gestionnaire - Site,Nombre total de logements,Nombre de logements PMR,Nombre de logements en collocation,T1,T1 bis,T2,T3,T4 et plus,Statut de la résidence
12345,First residence,Résidence Universitaire conventionnée,10 Rue de la Paix,Paris,75002,48.8698,2.3311,Example Manager,http://first.com,100,5,10,20,10,30,15,10,En service
67890,Second residence,Résidence sociale Jeunes Actifs,14 Boulevard de la Libération,Marseille,13001,43.2965,5.3698,Another Manager,http://second.com,150,10,5,25,20,40,10,30,En Service
abcde,Third planned residence,Résidence sociale Jeunes Actifs,10 Rue de la République,Lyon,69001,45.7570,4.8320,Another Manager,http://second.com,120,8,12,18,15,30,10,25,En projet
"""
    with mock.patch("builtins.open", mock.mock_open(read_data=csv_data)):
        call_command("import_CLEF", file="mocked_file", write=True)

    accommodation1 = Accommodation.objects.get(name="First residence")
    accommodation2 = Accommodation.objects.get(name="Second residence")
    accommodation3 = Accommodation.objects.get(name="Third planned residence")

    assert accommodation1.residence_type == "universitaire-conventionnee"
    assert accommodation1.address == "10 Rue de la Paix"
    assert accommodation1.city == "Paris"
    assert accommodation1.postal_code == "75002"
    assert accommodation1.geom is not None
    assert accommodation1.geom.x == 2.3311
    assert accommodation1.geom.y == 48.8698
    assert accommodation1.owner_name == "Example Manager"
    assert accommodation1.owner_url == "http://first.com"
    assert accommodation1.nb_total_apartments == 100
    assert accommodation1.nb_accessible_apartments == 5
    assert accommodation1.nb_coliving_apartments == 10
    assert accommodation1.nb_t1 == 20
    assert accommodation1.nb_t1_bis == 10
    assert accommodation1.nb_t2 == 30
    assert accommodation1.nb_t3 == 15
    assert accommodation1.nb_t4_more == 10
    assert accommodation1.published is True

    assert accommodation2.residence_type == "sociale-jeunes-actifs"
    assert accommodation2.address == "14 Boulevard de la Libération"
    assert accommodation2.city == "Marseille"
    assert accommodation2.postal_code == "13001"
    assert accommodation2.geom is not None
    assert accommodation2.geom.x == 5.3698
    assert accommodation2.geom.y == 43.2965
    assert accommodation2.owner_name == "Another Manager"
    assert accommodation2.owner_url == "http://second.com"
    assert accommodation2.nb_total_apartments == 150
    assert accommodation2.nb_accessible_apartments == 10
    assert accommodation2.nb_coliving_apartments == 5
    assert accommodation2.nb_t1 == 25
    assert accommodation2.nb_t1_bis == 20
    assert accommodation2.nb_t2 == 40
    assert accommodation2.nb_t3 == 10
    assert accommodation2.nb_t4_more == 30
    assert accommodation2.published is True

    assert accommodation3.published is False


@pytest.fixture
def mock_settings(settings):
    settings.OMOGEN_API_HOST = "api.example.com"
    settings.OMOGEN_API_CLIENT_ID = "client_id"
    settings.OMOGEN_API_CLIENT_SECRET = "client_secret"
    settings.OMOGEN_API_API_KEY = "api_key"
    return settings


@pytest.mark.django_db
def test_import_clef_command(mock_settings):
    with requests_mock.Mocker() as mocker:
        mocker.post(
            f"https://{mock_settings.OMOGEN_API_HOST}/auth-test/token",
            json={"access_token": "test_token"},
        )

        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/v1/external/getResidences",
            json=[
                {
                    "id": 1,
                    "nom": "Résidence Test",
                    "adresse": "1 rue de l'Epargne",
                    "ville": "Lyon",
                    "codePostal": "69001",
                    "typeResidence": "universitaire-conventionnee",
                    "typeGestionnaireId": 10,
                    "longitude": 2.0,
                    "latitude": 48.0,
                    "imageIds": [100, 101],
                    "nbTotalLogements": 100,
                    "nbLogementsAccessibles": 10,
                    "nbLogementsColiving": 5,
                    "nbT1": 50,
                    "nbT1Bis": 20,
                    "nbT2": 15,
                    "nbT3": 10,
                    "nbT4EtPlus": 5,
                }
            ],
        )

        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/v1/images/100",
            content=b"image_data_100",
        )
        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/v1/images/101",
            content=b"image_data_101",
        )

        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/v1/type-gestionnaires/10",
            json={"nom": "Bailleur Test", "url": "http://bailleur.test"},
        )

        call_command("import_CLEF_via_OMOGEN_API")

        accommodation = Accommodation.objects.get(name="Résidence Test")
        assert accommodation.address == "1 rue de l'Epargne"
        assert accommodation.city == "Lyon"
        assert accommodation.postal_code == "69001"
        assert accommodation.residence_type == "universitaire-conventionnee"
        assert accommodation.geom == Point(2.0, 48.0)
        assert accommodation.images == [b"image_data_100", b"image_data_101"]
        assert accommodation.nb_total_apartments == 100
        assert accommodation.nb_accessible_apartments == 10
        assert accommodation.nb_coliving_apartments == 5
        assert accommodation.nb_t1 == 50
        assert accommodation.nb_t1_bis == 20
        assert accommodation.nb_t2 == 15
        assert accommodation.nb_t3 == 10
        assert accommodation.nb_t4_more == 5

        owner = Owner.objects.get(name="Bailleur Test")
        assert owner.url == "http://bailleur.test"
        assert accommodation.owner == owner

        user = User.objects.get(username=...)
        assert user.is_active is False
        assert accommodation.owner.user == user

        external_source = ExternalSource.objects.get(accommodation=accommodation)
        assert external_source.source_id == "1"
        assert external_source.source == "clef"
