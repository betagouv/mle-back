from unittest import mock

import pytest
from django.core.management import call_command

from accommodation.models import Accommodation


@pytest.mark.django_db
def test_residence_type_mapping():
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
