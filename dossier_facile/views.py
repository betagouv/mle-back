import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Student
from dossier_facile.event_processor import DossierFacileWebhookEventProcessor
from dossier_facile.models import DossierFacileApplication, DossierFacileOAuthState, DossierFacileTenant
from dossier_facile.serializers import ApplicationSerializer, ApplyForHousingSerializer
from dossier_facile.services import DossierFacileClient, DossierFacileClientError
from dossier_facile.use_cases import apply_for_housing

logger = logging.getLogger(__name__)


class DossierFacileWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if not request.headers.get("X-Api-Key") == settings.DOSSIERFACILE_WEBHOOK_API_KEY:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        processor = DossierFacileWebhookEventProcessor(request.data)
        processed = processor.process_event()
        if not processed:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class StudentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(_get_student_for_user(request.user))


class OwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.owners.exists()


class ApplyForHousingView(APIView):
    authentication_classes = [permissions.IsAuthenticated]
    serializer_class = ApplyForHousingSerializer
    permission_classes = [StudentPermission]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            with transaction.atomic():
                application = apply_for_housing(
                    request.user.student, validated_data["accommodation"], validated_data["appartment_type"]
                )
                return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)
        except ValueError:
            logger.exception("Invalid Dossier Facile housing application payload.")
            return Response(
                {"detail": "Invalid data provided.", "type": "invalid_data"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApplicationsPerOwnerListView(ListAPIView):
    authentication_classes = [permissions.IsAuthenticated]
    permission_classes = [OwnerPermission]
    serializer_class = ApplicationSerializer
    queryset = DossierFacileApplication.objects.all()

    def get_queryset(self):
        return self.queryset.filter(accommodation__owner=self.request.user.owners.first())


def _get_student_for_user(user):
    if not user or not user.is_authenticated:
        return None

    return Student.objects.filter(user=user).first()


def _extract_tenant_id(profile: dict) -> str | None:
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


def _normalize_tenant_status(raw_status: str | None) -> str | None:
    if not raw_status:
        return None

    allowed_statuses = {choice for choice, _ in DossierFacileTenant.DossierFacileTenantStatus.choices}
    return raw_status if raw_status in allowed_statuses else None


def _extract_tenant_name(profile: dict, student) -> str:
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


def _extract_sharing_data(profile: dict) -> dict:
    apartment_sharing = profile.get("apartmentSharing")
    if not isinstance(apartment_sharing, dict):
        apartment_sharing = {}

    return {
        "status": apartment_sharing.get("status") or profile.get("status"),
        "url": apartment_sharing.get("dossierUrl") or profile.get("dossierUrl"),
        "pdf_url": apartment_sharing.get("dossierPdfUrl") or profile.get("dossierPdfUrl"),
    }


class DossierFacileConnectUrlView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        student = _get_student_for_user(request.user)
        if not student:
            return Response(
                {"detail": "Only student accounts can connect Dossier Facile.", "type": "not_student"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            client = DossierFacileClient()
        except ImproperlyConfigured:
            return Response(
                {"detail": "Dossier Facile integration is not configured.", "type": "dossier_facile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        state = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(seconds=settings.DOSSIERFACILE_STATE_TTL_SECONDS)

        with transaction.atomic():
            DossierFacileOAuthState.objects.filter(user=request.user).delete()
            DossierFacileOAuthState.objects.create(user=request.user, state=state, expires_at=expires_at)

        authorization_url = client.build_authorization_url(state=state, login_hint=request.user.email)
        return Response(
            {
                "authorization_url": authorization_url,
                "expires_at": expires_at,
            },
            status=status.HTTP_200_OK,
        )


class DossierFacileCallbackView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code or not state:
            return Response(
                {"detail": "Missing code or state parameter.", "type": "missing_oauth_parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                oauth_state = (
                    DossierFacileOAuthState.objects.select_related("user").select_for_update().get(state=state)
                )
                if oauth_state.is_expired():
                    oauth_state.delete()
                    return Response(
                        {"detail": "Expired Dossier Facile state parameter.", "type": "expired_state"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user = oauth_state.user
                oauth_state.delete()
        except DossierFacileOAuthState.DoesNotExist:
            return Response(
                {"detail": "Invalid Dossier Facile state parameter.", "type": "invalid_state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = _get_student_for_user(user)
        if not student:
            return Response(
                {"detail": "No student account is linked to this Dossier Facile state.", "type": "not_student"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = DossierFacileClient()
            access_token = client.exchange_code_for_token(code)
            profile = client.get_user_dossier(access_token)
        except ImproperlyConfigured:
            return Response(
                {"detail": "Dossier Facile integration is not configured.", "type": "dossier_facile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DossierFacileClientError as exc:
            return Response({"detail": exc.message, "type": exc.error_type}, status=exc.status_code)

        tenant_id = _extract_tenant_id(profile)
        if not tenant_id:
            return Response(
                {"detail": "Dossier Facile response did not include a tenant identifier.", "type": "invalid_profile"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        sharing_data = _extract_sharing_data(profile)
        tenant, _ = DossierFacileTenant.objects.update_or_create(
            student=student,
            tenant_id=tenant_id,
            defaults={
                "name": _extract_tenant_name(profile, student),
                "status": _normalize_tenant_status(sharing_data["status"]),
                "url": sharing_data["url"],
                "pdf_url": sharing_data["pdf_url"],
                "last_synced_at": timezone.now(),
            },
        )

        return Response(
            {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "status": tenant.status,
                "url": tenant.url,
                "pdf_url": tenant.pdf_url,
                "last_synced_at": tenant.last_synced_at,
            },
            status=status.HTTP_200_OK,
        )
