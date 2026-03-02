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
)
class DossierFacileOAuthAPITests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.connect_url = reverse("dossier-facile-connect-url")
        self.callback_url = reverse("dossier-facile-callback")

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

    def test_callback_returns_400_and_deletes_expired_state(self):
        user, _student = self._create_student_user()
        DossierFacileOAuthState.objects.create(
            user=user,
            state="expired-state",
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        response = self.client.get(self.callback_url, {"code": "oauth-code", "state": "expired-state"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["type"], "expired_state")
        self.assertFalse(DossierFacileOAuthState.objects.filter(state="expired-state").exists())

    @patch("dossier_facile.views.DossierFacileClient.get_user_dossier")
    @patch("dossier_facile.views.DossierFacileClient.exchange_code_for_token")
    def test_callback_creates_tenant_on_happy_path(self, mock_exchange_code_for_token, mock_get_user_dossier):
        user, student = self._create_student_user()
        DossierFacileOAuthState.objects.create(
            user=user,
            state="valid-state",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        mock_exchange_code_for_token.return_value = "access-token"
        mock_get_user_dossier.return_value = {
            "id": "tenant-123",
            "fullName": "Jane Doe",
            "status": "verified",
            "dossierUrl": "https://example.com/dossier",
            "dossierPdfUrl": "https://example.com/dossier.pdf",
        }

        response = self.client.get(self.callback_url, {"code": "oauth-code", "state": "valid-state"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(DossierFacileOAuthState.objects.filter(state="valid-state").exists())

        tenant = DossierFacileTenant.objects.get(student=student, tenant_id="tenant-123")
        self.assertEqual(tenant.name, "Jane Doe")
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.VERIFIED)
        self.assertEqual(tenant.url, "https://example.com/dossier")
        self.assertEqual(tenant.pdf_url, "https://example.com/dossier.pdf")

    @patch("dossier_facile.views.DossierFacileClient.get_user_dossier")
    @patch("dossier_facile.views.DossierFacileClient.exchange_code_for_token")
    def test_callback_updates_existing_tenant_instead_of_creating_duplicate(
        self,
        mock_exchange_code_for_token,
        mock_get_user_dossier,
    ):
        user, student = self._create_student_user()
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Old Name",
            status=DossierFacileTenant.DossierFacileTenantStatus.ACTIVE,
            url="https://example.com/old",
            pdf_url="https://example.com/old.pdf",
        )
        DossierFacileOAuthState.objects.create(
            user=user,
            state="valid-state-2",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        mock_exchange_code_for_token.return_value = "access-token"
        mock_get_user_dossier.return_value = {
            "id": "tenant-123",
            "fullName": "Updated Name",
            "status": "inactive",
            "dossierUrl": "https://example.com/new",
            "dossierPdfUrl": "https://example.com/new.pdf",
        }

        response = self.client.get(self.callback_url, {"code": "oauth-code", "state": "valid-state-2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DossierFacileTenant.objects.filter(student=student, tenant_id="tenant-123").count(), 1)

        tenant.refresh_from_db()
        self.assertEqual(tenant.name, "Updated Name")
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.INACTIVE)
        self.assertEqual(tenant.url, "https://example.com/new")
        self.assertEqual(tenant.pdf_url, "https://example.com/new.pdf")
