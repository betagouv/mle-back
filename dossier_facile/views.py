import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.shortcuts import redirect
from rest_framework import status
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from dossier_facile.event_processor import DossierFacileWebhookEventProcessor
from dossier_facile.models import DossierFacileApplication
from dossier_facile.serializers import ApplicationSerializer, ApplyForHousingSerializer, DossierFacileSyncSerializer
from dossier_facile.services import (
    DossierFacileClient,
    DossierFacileClientError,
    DossierFacileOAuthStateError,
    build_frontend_callback_url,
    consume_oauth_state,
    create_oauth_state_for_user,
    get_student_for_user,
    sync_tenant_from_code,
)
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
        return bool(get_student_for_user(request.user))


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


class DossierFacileConnectUrlView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        student = get_student_for_user(request.user)
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

        oauth_state = create_oauth_state_for_user(request.user)

        authorization_url = client.build_authorization_url(state=oauth_state.state, login_hint=request.user.email)
        return Response(
            {
                "authorization_url": authorization_url,
                "expires_at": oauth_state.expires_at,
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
            return redirect(build_frontend_callback_url(False, error_type="missing_oauth_parameters"))

        try:
            user = consume_oauth_state(state)
        except DossierFacileOAuthStateError as exc:
            return redirect(build_frontend_callback_url(False, error_type=exc.error_type))

        student = get_student_for_user(user)
        if not student:
            return redirect(build_frontend_callback_url(False, error_type="not_student"))

        try:
            tenant = sync_tenant_from_code(student, code)
        except ImproperlyConfigured:
            return redirect(build_frontend_callback_url(False, error_type="dossier_facile_not_configured"))
        except DossierFacileClientError as exc:
            return redirect(build_frontend_callback_url(False, error_type=exc.error_type))

        return redirect(
            build_frontend_callback_url(
                True,
                tenant_id=tenant.tenant_id,
                status=tenant.status,
            )
        )


class DossierFacileSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DossierFacileSyncSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        student = get_student_for_user(request.user)
        if not student:
            return Response(
                {"detail": "Only student accounts can sync Dossier Facile.", "type": "not_student"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tenant = sync_tenant_from_code(student, serializer.validated_data["code"])
        except ImproperlyConfigured:
            return Response(
                {"detail": "Dossier Facile integration is not configured.", "type": "dossier_facile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DossierFacileClientError as exc:
            return Response({"detail": exc.message, "type": exc.error_type}, status=exc.status_code)

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
