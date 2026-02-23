import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from notifications.exceptions import EmailDeliveryError
from notifications.factories import get_email_gateway
from notifications.services import send_reset_password

from account.models import Student

logger = logging.getLogger(__name__)


def build_password_reset_link(user, frontend_base_url: str) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)

    return f"{frontend_base_url}/reinitialiser-son-mot-de-passe?uid={uid}&token={token}"


def request_password_reset(email: str) -> None:
    student = Student.objects.filter(user__email=email).first()
    if not student:
        return
    password_reset_link = build_password_reset_link(student.user, f"{settings.FRONT_SITE_URL}")
    email_gateway = get_email_gateway()
    try:
        send_reset_password(student.user, password_reset_link, email_gateway)
    except EmailDeliveryError:
        logger.error(f"Failed to send password reset link to user {student.user.email}")


class DossierFacileServiceError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


def _validate_dossierfacile_configuration() -> None:
    required_settings = [
        "DOSSIERFACILE_CLIENT_ID",
        "DOSSIERFACILE_CLIENT_SECRET",
        "DOSSIERFACILE_AUTHORIZE_URL",
        "DOSSIERFACILE_TOKEN_URL",
        "DOSSIERFACILE_TENANT_PROFILE_URL",
        "DOSSIERFACILE_REDIRECT_URI",
    ]
    missing = [name for name in required_settings if not getattr(settings, name, None)]
    if missing:
        raise ImproperlyConfigured(f"Missing DossierFacile settings: {', '.join(missing)}")


def build_dossierfacile_authorization_url(email: str, state: str) -> str:
    _validate_dossierfacile_configuration()

    params = {
        "client_id": settings.DOSSIERFACILE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.DOSSIERFACILE_REDIRECT_URI,
        "scope": settings.DOSSIERFACILE_SCOPE,
        "state": state,
    }
    if email:
        params["login_hint"] = email

    return f"{settings.DOSSIERFACILE_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_dossierfacile_code_for_token(code: str) -> str:
    _validate_dossierfacile_configuration()

    try:
        response = requests.post(
            settings.DOSSIERFACILE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DOSSIERFACILE_REDIRECT_URI,
            },
            auth=(settings.DOSSIERFACILE_CLIENT_ID, settings.DOSSIERFACILE_CLIENT_SECRET),
            timeout=settings.DOSSIERFACILE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise DossierFacileServiceError(
            "Unable to reach DossierFacile token endpoint.",
            error_type="dossierfacile_token_endpoint_unreachable",
            status_code=502,
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        error_type = "dossierfacile_token_exchange_failed"
        status_code = 400 if response.status_code in (400, 401) else 502
        raise DossierFacileServiceError(
            payload.get("error_description") or "Unable to exchange DossierFacile authorization code.",
            error_type=error_type,
            status_code=status_code,
        )

    access_token = payload.get("access_token")
    if not access_token:
        raise DossierFacileServiceError(
            "DossierFacile did not return an access token.",
            error_type="dossierfacile_invalid_token_response",
            status_code=502,
        )

    return access_token


def fetch_dossierfacile_tenant_profile(access_token: str) -> dict:
    _validate_dossierfacile_configuration()

    try:
        response = requests.get(
            settings.DOSSIERFACILE_TENANT_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=settings.DOSSIERFACILE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise DossierFacileServiceError(
            "Unable to reach DossierFacile profile endpoint.",
            error_type="dossierfacile_profile_endpoint_unreachable",
            status_code=502,
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        raise DossierFacileServiceError(
            payload.get("error_description") or "Unable to fetch DossierFacile tenant profile.",
            error_type="dossierfacile_profile_fetch_failed",
            status_code=502,
        )

    if not isinstance(payload, dict):
        raise DossierFacileServiceError(
            "Invalid DossierFacile tenant profile format.",
            error_type="dossierfacile_invalid_profile_response",
            status_code=502,
        )

    return payload


def extract_dossierfacile_tenant_id(profile: dict) -> str | None:
    for key in ("connectedTenantId", "id", "tenant_id", "tenantId", "sub"):
        value = profile.get(key)
        if value:
            return str(value)

    apartment_sharing = profile.get("apartmentSharing")
    if isinstance(apartment_sharing, dict):
        for key in ("tenantId", "tenant_id", "id"):
            value = apartment_sharing.get(key)
            if value:
                return str(value)

    return None


def extract_dossierfacile_sharing_data(profile: dict) -> dict:
    apartment_sharing = profile.get("apartmentSharing")
    if not isinstance(apartment_sharing, dict):
        apartment_sharing = {}

    return {
        "status": apartment_sharing.get("status") or profile.get("status"),
        "dossier_url": apartment_sharing.get("dossierUrl") or profile.get("dossierUrl"),
        "dossier_pdf_url": apartment_sharing.get("dossierPdfUrl") or profile.get("dossierPdfUrl"),
    }
