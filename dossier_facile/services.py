from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class DossierFacileClientError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int = 502):
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
