import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from accommodation.models import Accommodation
from tests.account.factories import OwnerFactory


@pytest.mark.django_db
class TestAccommodation:
    def test_valid_accommodation_saves_correctly(self):
        acc = Accommodation(
            name="Résidence A",
            address="1 rue test",
            city="Paris",
            postal_code="75000",
            geom=Point(2.35, 48.85),
            nb_t1=5,
            nb_t1_available=3,
        )
        acc.full_clean()
        acc.save()
        assert acc.nb_t1_available == 3

    def test_raises_error_if_nb_t1_available_exceeds_nb_t1(self):
        acc = Accommodation(
            name="Résidence B",
            address="2 rue test",
            city="Lyon",
            postal_code="69000",
            geom=Point(4.85, 45.75),
            nb_t1=5,
            nb_t1_available=6,
        )
        with pytest.raises(ValidationError) as e:
            acc.full_clean()
        assert "nb_t1_available" in e.value.message_dict

    def test_raises_error_if_owner_and_external_reference_are_not_unique(self):
        owner = OwnerFactory()

        Accommodation.objects.create(
            owner=owner,
            external_reference="1234567890",
            name="Résidence A",
            address="1 rue test",
            city="Lyon",
            postal_code="69000",
            geom=Point(4.85, 45.75),
            nb_t1=5,
            nb_t1_available=5,
        )

        acc = Accommodation(
            owner=owner,
            external_reference="1234567890",
            name="Résidence B",
            address="2 rue test",
            city="Lyon",
            postal_code="69000",
            geom=Point(4.85, 45.75),
            nb_t1=5,
            nb_t1_available=5,
        )

        with pytest.raises(ValidationError) as e:
            acc.full_clean()

        assert any(
            "Un objet Résidence avec ces champs Owner et External reference existe déjà." in msg
            for msg in e.value.messages
        )
