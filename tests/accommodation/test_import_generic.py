import pytest
from django.core.management import call_command

from accommodation.models import Accommodation
from tests.territories.factories import AcademyFactory, DepartmentFactory


@pytest.mark.django_db
def test_nominal(tmp_path):
    academy = AcademyFactory(name="France")
    DepartmentFactory(code="75", academy=academy)
    DepartmentFactory(code="69", academy=academy)

    csv_data = """name;address;city;postal_code;residence_type;latitude;longitude;owner_name;owner_url;nb_total_apartments;nb_accessible_apartments;nb_coliving_apartments;nb_t1;t1_rent_min;t1_rent_max;nb_t1_bis;t1_bis_rent_min;t1_bis_rent_max;nb_t2;t2_rent_min;t2_rent_max;nb_t3;t3_rent_min;t3_rent_max;nb_t4_more;t4_more_rent_min;t4_more_rent_max;pictures;laundry_room;common_areas;bike_storage;parking;secure_access;residence_manager;kitchen_type;desk;cooking_plates;microwave;refrigerator;bathroom;description\n"Résidence Alpha";"10 rue de Paris";"Paris";"75001";"universitaire-conventionnee";48.8566;2.3522;"Bailleur Alpha";"https://alpha.fr";100;10;20;30;400.0;600.0;10;500.0;700.0;20;600.0;800.0;10;700.0;900.0;5;800.0;1000.0;"https://image.com/pic1.jpg|https://image.com/pic2.jpg";TRUE;TRUE;TRUE;TRUE;TRUE;FALSE;"private";TRUE;TRUE;TRUE;TRUE;"private";""\n"Résidence Beta";"5 avenue de Lyon";"Lyon";"69002";"mixte-actifs-etudiants";45.764;4.8357;"Bailleur Beta";"https://beta.fr";80;5;15;20;350.0;550.0;8;450.0;650.0;15;550.0;750.0;7;650.0;850.0;3;750.0;950.0;"https://image.com/pic3.jpg|https://image.com/pic4.jpg";FALSE;TRUE;TRUE;FALSE;TRUE;TRUE;"shared";FALSE;TRUE;FALSE;TRUE;"shared";"Réservée aux jeunes actifs."
"""

    csv_file = tmp_path / "residences.csv"
    csv_file.write_text(csv_data, encoding="utf-8")

    call_command("import_generic", file=str(csv_file), source="test_source", skip_images=True)

    accommodation1 = Accommodation.objects.get(name="Résidence Alpha")
    accommodation2 = Accommodation.objects.get(name="Résidence Beta")

    assert accommodation1.residence_type == "universitaire-conventionnee"
    assert accommodation1.address == "10 rue de Paris"
    assert accommodation1.postal_code == "75001"
    assert accommodation1.geom.x == 2.3522
    assert accommodation1.geom.y == 48.8566

    assert accommodation2.residence_type == "mixte-actifs-etudiants"
    assert accommodation2.address == "5 avenue de Lyon"
    assert accommodation2.postal_code == "69002"
    assert accommodation2.geom.x == 4.8357
    assert accommodation2.geom.y == 45.764
    assert accommodation2.description == "Réservée aux jeunes actifs."
