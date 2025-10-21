from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import OwnerFactory, UserFactory


class AccountAPITests(APITestCase):
    @pytest.mark.django_db
    def test_owner_list_view(self):
        OwnerFactory.create_batch(5)
        response = self.client.get(reverse("owner-list"))
        assert response.status_code == 200
        assert len(response.json()) == 5

    @patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email")
    def test_request_magic_link(self, mock_send_email):
        mock_send_email.return_value = None

        response = self.client.post(reverse("request-magic-link"), {"email": "test@test.com"})
        assert response.status_code == 200
        assert response.json() == {
            "detail": "If an account exists with this email, you will receive a link to log in. Please contact xxx in case of problem."
        }

        UserFactory.create(email="test@test.com")
        response = self.client.post(reverse("request-magic-link"), {"email": "test@test.com"})
        assert response.status_code == 200
        assert response.json() == {
            "detail": "If an account exists with this email, you will receive a link to log in. Please contact xxx in case of problem."
        }
        assert mock_send_email.call_count == 1
