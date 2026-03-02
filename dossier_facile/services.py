import secrets
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from account.models import Student
from dossier_facile.models import DossierFacileOAuthState, DossierFacileTenant


class DossierFacileClientError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


class DossierFacileOAuthStateError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


class DossierFacileClient:
    def __init__(self):
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        required_settings = [
            "DOSSIERFACILE_CLIENT_ID",
            "DOSSIERFACILE_CLIENT_SECRET",
            "DOSSIERFACILE_AUTHORIZE_URL",
            "DOSSIERFACILE_TOKEN_URL",
            "DOSSIERFACILE_TENANT_PROFILE_URL",
            "DOSSIERFACILE_REDIRECT_URI",
        ]
        missing_settings = [name for name in required_settings if not getattr(settings, name, None)]
        if missing_settings:
            raise ImproperlyConfigured(f"Missing DossierFacile settings: {', '.join(missing_settings)}")

    def build_authorization_url(self, state: str, login_hint: str | None = None) -> str:
        params = {
            "client_id": settings.DOSSIERFACILE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.DOSSIERFACILE_REDIRECT_URI,
            "scope": settings.DOSSIERFACILE_SCOPE,
            "state": state,
        }
        if login_hint:
            params["login_hint"] = login_hint

        return f"{settings.DOSSIERFACILE_AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> str:
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
            raise DossierFacileClientError(
                "Unable to reach Dossier Facile token endpoint.",
                error_type="dossier_facile_token_endpoint_unreachable",
                status_code=502,
            ) from exc

        payload = self._safe_json(response)
        if response.status_code >= 400:
            raise DossierFacileClientError(
                payload.get("error_description") or "Unable to exchange Dossier Facile authorization code.",
                error_type="dossier_facile_token_exchange_failed",
                status_code=400 if response.status_code in (400, 401) else 502,
            )

        access_token = payload.get("access_token")
        if not access_token:
            raise DossierFacileClientError(
                "Dossier Facile did not return an access token.",
                error_type="dossier_facile_invalid_token_response",
                status_code=502,
            )

        return access_token

    def get_user_dossier(self, access_token: str) -> dict:
        try:
            response = requests.get(
                settings.DOSSIERFACILE_TENANT_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=settings.DOSSIERFACILE_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise DossierFacileClientError(
                "Unable to reach Dossier Facile profile endpoint.",
                error_type="dossier_facile_profile_endpoint_unreachable",
                status_code=502,
            ) from exc

        payload = self._safe_json(response)
        if response.status_code >= 400:
            raise DossierFacileClientError(
                payload.get("error_description") or "Unable to fetch Dossier Facile dossier.",
                error_type="dossier_facile_profile_fetch_failed",
                status_code=502,
            )
        if not isinstance(payload, dict):
            raise DossierFacileClientError(
                "Invalid Dossier Facile profile format.",
                error_type="dossier_facile_invalid_profile_response",
                status_code=502,
            )

        return payload

    @staticmethod
    def _safe_json(response) -> dict:
        try:
            payload = response.json()
        except ValueError:
            return {}

        return payload if isinstance(payload, dict) else {}


def get_student_for_user(user):
    if not user or not user.is_authenticated:
        return None

    return Student.objects.filter(user=user).first()


def get_latest_tenant_for_student(student):
    if not student:
        return None

    return student.dossier_facile_tenants.order_by("-updated_at", "-created_at").first()


def create_oauth_state_for_user(user) -> DossierFacileOAuthState:
    state = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(seconds=settings.DOSSIERFACILE_STATE_TTL_SECONDS)

    with transaction.atomic():
        DossierFacileOAuthState.objects.filter(user=user).delete()
        return DossierFacileOAuthState.objects.create(user=user, state=state, expires_at=expires_at)


def consume_oauth_state(state: str):
    try:
        with transaction.atomic():
            oauth_state = DossierFacileOAuthState.objects.select_related("user").select_for_update().get(state=state)
            if oauth_state.is_expired():
                oauth_state.delete()
                expired = True
            else:
                expired = False
                user = oauth_state.user
                oauth_state.delete()

    except DossierFacileOAuthState.DoesNotExist as exc:
        raise DossierFacileOAuthStateError(
            "Invalid Dossier Facile state parameter.",
            error_type="invalid_state",
            status_code=400,
        ) from exc

    if expired:
        raise DossierFacileOAuthStateError(
            "Expired Dossier Facile state parameter.",
            error_type="expired_state",
            status_code=400,
        )

    return user


def cleanup_expired_oauth_states() -> int:
    return DossierFacileOAuthState.objects.filter(expires_at__lte=timezone.now()).delete()[0]


def normalize_tenant_status(raw_status: str | None) -> str | None:
    if not raw_status:
        return None

    normalized_status = raw_status.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "validated": DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        "verified_account": DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        "deleted_account": DossierFacileTenant.DossierFacileTenantStatus.ACCESS_REVOKED,
    }
    normalized_status = aliases.get(normalized_status, normalized_status)

    allowed_statuses = {choice for choice, _ in DossierFacileTenant.DossierFacileTenantStatus.choices}
    return normalized_status if normalized_status in allowed_statuses else None


def extract_tenant_id(profile: dict) -> str | None:
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


def extract_tenant_name(profile: dict, student) -> str:
    for key in ("fullName", "name"):
        value = profile.get(key)
        if value:
            return str(value)

    first_name = profile.get("firstName")
    last_name = profile.get("lastName")
    if first_name or last_name:
        return f"{first_name or ''} {last_name or ''}".strip()

    full_name = student.user.get_full_name().strip()
    if full_name:
        return full_name

    return student.user.email or student.user.username


def extract_sharing_data(profile: dict) -> dict:
    apartment_sharing = profile.get("apartmentSharing")
    if not isinstance(apartment_sharing, dict):
        apartment_sharing = {}

    return {
        "status": normalize_tenant_status(apartment_sharing.get("status") or profile.get("status")),
        "url": apartment_sharing.get("dossierUrl") or profile.get("dossierUrl"),
        "pdf_url": apartment_sharing.get("dossierPdfUrl") or profile.get("dossierPdfUrl"),
    }


def sync_tenant_from_profile(student, profile: dict) -> DossierFacileTenant:
    tenant_id = extract_tenant_id(profile)
    if not tenant_id:
        raise DossierFacileClientError(
            "Dossier Facile response did not include a tenant identifier.",
            error_type="invalid_profile",
            status_code=502,
        )

    sharing_data = extract_sharing_data(profile)
    tenant, _ = DossierFacileTenant.objects.update_or_create(
        student=student,
        tenant_id=tenant_id,
        defaults={
            "name": extract_tenant_name(profile, student),
            "status": sharing_data["status"],
            "url": sharing_data["url"],
            "pdf_url": sharing_data["pdf_url"],
            "last_synced_at": timezone.now(),
        },
    )
    return tenant


def sync_tenant_from_code(student, code: str) -> DossierFacileTenant:
    client = DossierFacileClient()
    access_token = client.exchange_code_for_token(code)
    profile = client.get_user_dossier(access_token)
    return sync_tenant_from_profile(student, profile)


def build_frontend_callback_url(success: bool, **params) -> str:
    if success:
        base_url = getattr(settings, "DOSSIERFACILE_FRONTEND_SUCCESS_URL", "") or (
            f"{settings.FRONT_SITE_URL}/dossier-facile/success"
        )
    else:
        base_url = getattr(settings, "DOSSIERFACILE_FRONTEND_ERROR_URL", "") or (
            f"{settings.FRONT_SITE_URL}/dossier-facile/error"
        )

    query_params = [(key, value) for key, value in params.items() if value is not None]
    if not query_params:
        return base_url

    split_url = urlsplit(base_url)
    merged_query = parse_qsl(split_url.query, keep_blank_values=True) + query_params
    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(merged_query),
            split_url.fragment,
        )
    )
