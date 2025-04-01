from unittest import mock

import pytest
import requests_mock
from account.models import Owner
from accommodation.models import Accommodation, ExternalSource
from django.core.management import call_command

from tests.territories.factories import AcademyFactory, DepartmentFactory


@pytest.mark.django_db
def test_residence_type_mapping():
    academy = AcademyFactory(name="France")

    DepartmentFactory(code="75", academy=academy)
    DepartmentFactory(code="13", academy=academy)
    DepartmentFactory(code="69", academy=academy)

    csv_data = """Identifiant fonctionnel,Nom de la résidence,Type de résidence,Adresse administrative,Commune,Code postal,Latitude,Longitude,Gestionnaire - Nom,Gestionnaire - Site,Nombre total de logements,Nombre de logements PMR,Nombre de logements en collocation,T1,T1 bis,T2,T3,T4 et plus,Statut de la résidence
12345,First residence,Résidence Universitaire conventionnée,10 Rue de la Paix,Paris,75002,48.8698,2.3311,Example Manager,http://first.com,100,5,10,20,10,30,15,10,En service
67890,Second residence,Résidence Universitaire conventionnée,14 Boulevard de la Libération,Marseille,13001,43.2965,5.3698,Another Manager,http://second.com,150,10,5,25,20,40,10,30,En Service
abcde,Third planned residence,Résidence Universitaire conventionnée,10 Rue de la République,Lyon,69001,45.7570,4.8320,Another Manager,http://second.com,120,8,12,18,15,30,10,25,En projet
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
    assert accommodation1.owner.name == "Example Manager"
    assert accommodation1.owner.url == "http://first.com"
    assert accommodation1.nb_total_apartments == 100
    assert accommodation1.nb_accessible_apartments == 5
    assert accommodation1.nb_coliving_apartments == 10
    assert accommodation1.nb_t1 == 20
    assert accommodation1.nb_t1_bis == 10
    assert accommodation1.nb_t2 == 30
    assert accommodation1.nb_t3 == 15
    assert accommodation1.nb_t4_more == 10
    assert accommodation1.published is True

    assert accommodation2.residence_type == "universitaire-conventionnee"
    assert accommodation2.address == "14 Boulevard de la Libération"
    assert accommodation2.city == "Marseille"
    assert accommodation2.postal_code == "13001"
    assert accommodation2.geom is not None
    assert accommodation2.geom.x == 5.3698
    assert accommodation2.geom.y == 43.2965
    assert accommodation2.owner.name == "Another Manager"
    assert accommodation2.owner.url == "http://second.com"
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
    settings.OMOGEN_API_CLEF_APP_NAME = "clef-residence-pp"
    return settings


@pytest.mark.django_db
def test_import_clef_command(mock_settings):
    with requests_mock.Mocker() as mocker:
        mocker.post(
            f"https://{mock_settings.OMOGEN_API_HOST}/auth-test/token",
            json={"access_token": "test_token"},
        )

        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/clef-residence-pp/v1/external/getResidences",
            json={
                "content": [
                    {
                        "id": 6202,
                        "nom": "Residence AAA",
                        "adresseAdministrative": "2 rue des platanes 75009 Paris",
                        "adresseGeolocalisee": "2 Rue des platanes 75009 Paris",
                        "latitude": "48",
                        "longitude": "2",
                        "codePostal": "75005",
                        "gestionnaireNom": "ABC",
                        "gestionnaireSite": "https://abc.test",
                        "nombreTotalLogement": 100,
                        "nombreLogementPMR": 10,
                        "nombreT1": 50,
                        "nombreT1Bis": 20,
                        "nombreT2": 15,
                        "nombreT3": 10,
                        "nombreT4Plus": 5,
                        "nombreAutre": None,
                        "nombreTotalPlace": 100,
                        "nombreTotalPlaceConventionnees": 99,
                        "nombreTotalPlaceLoyerLibre": None,
                        "nombreTotalPlaceAutre": None,
                        "nombreTotalPlacePMR": 10,
                        "idTypeResidence": 2,
                        "codeCommune": "75056",
                        "codeAcademie": "01",
                        "idStatutResidence": 3,
                        "images": [100, 101],
                    },
                    {
                        "id": 4,
                        "nom": "Residence BBB",
                        "adresseAdministrative": "112 Rue des Chênes, 69120 Vaulx-en-Velin, France",
                        "adresseGeolocalisee": "112 Rue des Chênes, 69120 Vaulx-en-Velin, France",
                        "latitude": "45.680049",
                        "longitude": "5.0055474",
                        "codePostal": "69120",
                        "gestionnaireNom": "DEF",
                        "gestionnaireSite": "https://def.test",
                        "nombreTotalLogement": 200,
                        "nombreLogementCollocation": None,
                        "nombreLogementPMR": 12,
                        "nombreT1": 125,
                        "nombreT1Bis": 40,
                        "nombreT2": None,
                        "nombreT3": 10,
                        "nombreT4Plus": 5,
                        "nombreAutre": None,
                        "precisionAutre": None,
                        "nombreTotalPlace": 63,
                        "idTypeResidence": 2,
                        "codeCommune": "69256",
                        "codeAcademie": "10",
                        "idProprietaireType": None,
                        "idGestionnaireType": 2,
                        "idStatutResidence": 3,
                        "images": [],
                    },
                ],
                "pageable": {"sort": [], "pageNumber": 0, "pageSize": 20, "offset": 0, "paged": True, "unpaged": False},
                "totalElements": 2,
                "totalPages": 1,
                "last": True,
                "size": 20,
                "number": 0,
                "sort": [],
                "numberOfElements": 2,
                "first": True,
                "empty": False,
            },
        )

        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/clef-residence-pp/v1/images/100",
            content=b"image_data_100",
        )
        mocker.get(
            f"https://{mock_settings.OMOGEN_API_HOST}/clef-residence-pp/v1/images/101",
            content=b"image_data_101",
        )

        # mocker.get(
        #     f"https://{mock_settings.OMOGEN_API_HOST}/clef-referentiel-clef-pp/v1/type-gestionnaires/10",
        #     json={"nom": "Bailleur Test", "url": "http://bailleur.test"},
        # )

        mocker.get(
            "https://api-adresse.data.gouv.fr/search?q=2+Rue+des+platanes+75009+Paris",
            json={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [2, 48]},
                        "properties": {
                            "label": "2 Rue des platanes 75009 Paris",
                            "score": 0.5655894117647059,
                            "housenumber": "2",
                            "id": "75109_0509_00002",
                            "name": "2 Rue des platanes",
                            "postcode": "75009",
                            "city": "Paris",
                            "street": "Rue des platanes",
                        },
                    },
                ],
            },
        )

        mocker.get(
            "https://api-adresse.data.gouv.fr/search?q=112+Rue+des+Ch%C3%AAnes%2C+69120+Vaulx-en-Velin%2C+France",
            json={
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [4.934459, 45.779062]},
                        "properties": {
                            "label": "112 Rue des Chênes France 69120 Vaulx-en-Velin",
                            "score": 0.5401374025974026,
                            "id": "69256_0824",
                            "banId": "29361185-8f35-4dde-a5f4-8165377c5de0",
                            "name": "112 Rue des Chênes France",
                            "postcode": "69120",
                            "city": "Vaulx-en-Velin",
                            "type": "street",
                            "street": "112 Rue des Chênes France",
                        },
                    },
                ],
            },
        )
        mocker.post(
            f"https://{mock_settings.OMOGEN_API_HOST}/auth-test/token",
            json={"access_token": "test_token"},
        )

        call_command("import_CLEF_via_OMOGEN_API")

        accommodation = Accommodation.objects.get(name="Residence AAA")
        assert accommodation.address == "2 Rue des platanes"
        assert accommodation.city == "Paris"
        assert accommodation.postal_code == "75009"
        assert accommodation.residence_type == "universitaire-conventionnee"
        assert accommodation.geom.x == 2.0
        assert accommodation.geom.y == 48.0
        assert accommodation.images[0].tobytes() == b"image_data_100"
        assert accommodation.images[1].tobytes() == b"image_data_101"
        assert accommodation.nb_total_apartments == 100
        assert accommodation.nb_accessible_apartments == 10
        assert accommodation.nb_coliving_apartments is None
        assert accommodation.nb_t1 == 50
        assert accommodation.nb_t1_bis == 20
        assert accommodation.nb_t2 == 15
        assert accommodation.nb_t3 == 10
        assert accommodation.nb_t4_more == 5

        owner = Owner.objects.get(name="ABC")
        assert owner.url == "https://abc.test"
        assert accommodation.owner == owner
        assert owner.user.is_active is False

        external_source = ExternalSource.objects.get(accommodation=accommodation)
        assert external_source.source_id == "6202"
        assert external_source.source == "clef"

        accommodation = Accommodation.objects.get(name="Residence BBB")
        assert accommodation.address == "112 Rue des Chênes France"
        assert accommodation.city == "Vaulx-en-Velin"
        assert accommodation.postal_code == "69120"
        assert accommodation.residence_type == "universitaire-conventionnee"
        assert accommodation.geom.x == 4.934459
        assert accommodation.geom.y == 45.779062
        assert accommodation.images == []
        assert accommodation.nb_total_apartments == 200
        assert accommodation.nb_accessible_apartments == 12
        assert accommodation.nb_coliving_apartments is None
        assert accommodation.nb_t1 == 125
        assert accommodation.nb_t1_bis == 40
        assert accommodation.nb_t2 is None
        assert accommodation.nb_t3 == 10
        assert accommodation.nb_t4_more == 5

        owner = Owner.objects.get(name="DEF")
        assert owner.url == "https://def.test"
        assert accommodation.owner == owner
        assert owner.user.is_active is False

        external_source = ExternalSource.objects.get(accommodation=accommodation)
        assert external_source.source_id == "4"
        assert external_source.source == "clef"
