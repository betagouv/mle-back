import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import OwnerFactory


class AccountAPITests(APITestCase):
    @pytest.mark.django_db
    def test_owner_list_view(self):
        OwnerFactory.create_batch(5)
        response = self.client.get(reverse("owner-list"))
        assert response.status_code == 200
        assert len(response.json()) == 5
