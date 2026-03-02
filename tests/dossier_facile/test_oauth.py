from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Student
from dossier_facile.models import DossierFacileOAuthState, DossierFacileTenant


@override_settings(
    DOSSIERFACILE_CLIENT_ID="client-id",
    DOSSIERFACILE_CLIENT_SECRET="client-secret",
    DOSSIERFACILE_AUTHORIZE_URL="https://example.com/oauth/authorize",
    DOSSIERFACILE_TOKEN_URL="https://example.com/oauth/token",
    DOSSIERFACILE_TENANT_PROFILE_URL="https://example.com/api/me",
    DOSSIERFACILE_REDIRECT_URI="https://api.example.com/api/dossier-facile/callback/",
    DOSSIERFACILE_SCOPE="openid",
    DOSSIERFACILE_TIMEOUT_SECONDS=10,
    DOSSIERFACILE_STATE_TTL_SECONDS=600,
    FRONT_SITE_URL="https://frontend.example.com",
)
class DossierFacileOAuthAPITests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.connect_url = reverse("dossier-facile-connect-url")
        self.callback_url = reverse("dossier-facile-callback")
        self.sync_url = reverse("dossier-facile-sync")

    def _create_student_user(self, email="student@example.com"):
        user = self.user_model.objects.create_user(
            username=email,
            email=email,
            password="testpassword123",
            is_active=True,
        )
        student = Student.objects.create(user=user)
        return user, student

    def test_connect_url_creates_new_state_and_replaces_previous_one(self):
        user, _student = self._create_student_user()
        DossierFacileOAuthState.objects.create(
            user=user,
            state="old-state",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.connect_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DossierFacileOAuthState.objects.filter(user=user).count(), 1)

        oauth_state = DossierFacileOAuthState.objects.get(user=user)
        self.assertNotEqual(oauth_state.state, "old-state")

        authorization_url = response.json()["authorization_url"]
        query = parse_qs(urlparse(authorization_url).query)
        self.assertEqual(query["state"][0], oauth_state.state)
        self.assertEqual(query["client_id"][0], "client-id")
        self.assertEqual(query["redirect_uri"][0], "https://api.example.com/api/dossier-facile/callback/")

    def test_connect_url_rejects_non_student(self):
        user = self.user_model.objects.create_user(
            username="plain-user",
            email="plain@example.com",
            password="testpassword123",
            is_active=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.connect_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["type"], "not_student")

    def test_callback_redirects_to_error_when_state_is_expired(self):
        user, _student = self._create_student_user()
        DossierFacileOAuthState.objects.create(
            user=user,
            state="expired-state",
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = self.client.get(self.callback_url, {"code": "oauth-code", "state": "expired-state"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response["Location"],
            "https://frontend.example.com/dossier-facile/error?error_type=expired_state",
        )
        self.assertFalse(DossierFacileOAuthState.objects.filter(state="expired-state").exists())

    def test_callback_redirects_to_error_when_parameters_are_missing(self):
        response = self.client.get(self.callback_url, {"state": "missing-code"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response["Location"],
            "https://frontend.example.com/dossier-facile/error?error_type=missing_oauth_parameters",
        )

    @patch("dossier_facile.views.sync_tenant_from_code")
    def test_callback_redirects_to_success_on_happy_path(self, mock_sync_tenant_from_code):
        user, student = self._create_student_user()
        DossierFacileOAuthState.objects.create(
            user=user,
            state="valid-state",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
            url="https://example.com/dossier",
            pdf_url="https://example.com/dossier.pdf",
        )
        mock_sync_tenant_from_code.return_value = tenant

        response = self.client.get(self.callback_url, {"code": "oauth-code", "state": "valid-state"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response["Location"],
            "https://frontend.example.com/dossier-facile/success?tenant_id=tenant-123&status=verified",
        )
        self.assertFalse(DossierFacileOAuthState.objects.filter(state="valid-state").exists())
        mock_sync_tenant_from_code.assert_called_once_with(student, "oauth-code")

    @patch("dossier_facile.views.sync_tenant_from_code")
    def test_sync_returns_tenant_payload(self, mock_sync_tenant_from_code):
        user, student = self._create_student_user()
        self.client.force_authenticate(user=user)
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
            url="https://example.com/dossier",
            pdf_url="https://example.com/dossier.pdf",
        )
        mock_sync_tenant_from_code.return_value = tenant

        response = self.client.post(self.sync_url, {"code": "fresh-code"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["tenant_id"], "tenant-123")
        self.assertEqual(response.json()["status"], "verified")
        mock_sync_tenant_from_code.assert_called_once_with(student, "fresh-code")
