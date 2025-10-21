from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APITestCase
from sesame.utils import get_token

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


class VerifyMagicLinkAPITests(APITestCase):
    def test_verify_magic_link_success(self):
        user = UserFactory(is_active=True, is_staff=True)
        token = get_token(user)

        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": token})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_verify_magic_link_invalid(self):
        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": "invalidtoken"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid or expired token.")

    def test_verify_magic_link_missing_token(self):
        url = reverse("check-magic-link")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Token is required.")
