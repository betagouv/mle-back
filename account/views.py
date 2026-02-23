import logging
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from account.serializers import UserSerializer
from account.throttles import PasswordResetThrottle
from notifications.exceptions import EmailDeliveryError
from notifications.factories import get_email_gateway
from notifications.services import send_account_validation

from .models import Owner, Student, StudentRegistrationToken
from .serializers import (
    DossierFacileWebhookSerializer,
    OwnerSerializer,
    PasswordResetConfirmSerializer,
    StudentDossierFacileCompleteConnectSerializer,
    StudentDossierFacileStartConnectSerializer,
    StudentDossierFacileStatusSerializer,
    StudentGetTokenSerializer,
    StudentLogoutSerializer,
    StudentRegistrationSerializer,
    StudentRegistrationValidationSerializer,
    StudentRequestPasswordResetSerializer,
    StudentTokenResponseSerializer,
)
from .services import (
    DossierFacileServiceError,
    build_dossierfacile_authorization_url,
    exchange_dossierfacile_code_for_token,
    extract_dossierfacile_sharing_data,
    extract_dossierfacile_tenant_id,
    fetch_dossierfacile_tenant_profile,
    request_password_reset,
)

User = get_user_model()
logger = logging.getLogger(__name__)
DOSSIERFACILE_STATE_SALT = "dossierfacile-oauth-state"


class OwnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer


@extend_schema(
    summary="Register a new student",
    description="Register a new student with the given email, first name, last name and password.",
    request=StudentRegistrationSerializer,
    responses={201: {"message": "Student registered successfully"}},
)
class StudentRegistrationView(generics.GenericAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        registration_token = StudentRegistrationToken.get_or_create_for_user(student.user)

        validation_link = f"{settings.FRONT_SITE_URL}/verification?validation_token={registration_token.token}"

        email_gateway = get_email_gateway()
        try:
            send_account_validation(student.user, validation_link, email_gateway)
        except EmailDeliveryError:
            logger.error(f"Failed to send account validation link to user {student.user.email}")
        return Response({"message": "Student registered successfully"}, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Validate a student registration",
    description="Validate a student registration with the given token.",
    request=StudentRegistrationValidationSerializer,
    responses={200: {"message": "Student validated successfully"}},
)
class StudentRegistrationValidationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentRegistrationValidationSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                registration_token = StudentRegistrationToken.objects.select_for_update().get(
                    token=serializer.validated_data["validation_token"]
                )
                student = registration_token.student
                if student.user.is_active:
                    return Response(
                        {
                            "detail": "Student already validated",
                            "type": "already_validated",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                student.user.is_active = True
                student.user.save()
                registration_token.delete()
        except StudentRegistrationToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired validation token", "type": "invalid_or_expired_validation_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Student validated successfully"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get a token for a student",
    description="Get a token for a student with the given email and password.",
    request=StudentGetTokenSerializer,
    responses={200: StudentTokenResponseSerializer},
)
class StudentGetTokenView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = StudentGetTokenSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request, email=serializer.validated_data["email"], password=serializer.validated_data["password"]
        )
        if not user:
            return Response(
                {"detail": "Invalid email or password.", "type": "invalid_email_or_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {
                "access": access_token,
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Request a password reset",
    description="Request a password reset for a student with the given email.",
    request=StudentRequestPasswordResetSerializer,
    responses={
        200: OpenApiResponse(description="Password reset email sent if user exists"),
        429: OpenApiResponse(description="Too many requests – rate limit exceeded"),
    },
)
class StudentRequestPasswordResetView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentRequestPasswordResetSerializer
    throttle_classes = [PasswordResetThrottle]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_password_reset(serializer.validated_data["email"])

        return Response({"message": "Password reset email sent if user exists"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Confirm a password reset",
    description="Confirm a password reset for a student with the given uid, token and new password.",
    request=PasswordResetConfirmSerializer,
    responses={200: {"message": "Password reset successfully"}},
)
class StudentPasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    http_method_names = ["post"]

    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "Invalid reset link", "type": "invalid_reset_link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {"detail": "Invalid reset link", "type": "invalid_reset_link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password reset successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Logout a student",
    description="Logout a student with the given refresh token.",
    request=StudentLogoutSerializer,
    responses={200: {"message": "Logout successfully"}},
)
class StudentLogoutView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]
    serializer_class = StudentLogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid token.", "type": "invalid_token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logout successfully"}, status=status.HTTP_200_OK)


def _get_student_or_none(user):
    return Student.objects.filter(user=user).first()


@extend_schema(
    summary="Start DossierFacile link flow",
    description="Builds the DossierFacile authorization URL and signed state for the authenticated student.",
    responses={200: StudentDossierFacileStartConnectSerializer},
)
class StudentDossierFacileStartConnectView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if not _get_student_or_none(request.user):
            return Response(
                {"detail": "Only student accounts can link DossierFacile.", "type": "not_student"},
                status=status.HTTP_403_FORBIDDEN,
            )

        state = signing.dumps(
            {"user_id": request.user.id, "nonce": secrets.token_urlsafe(16)},
            salt=DOSSIERFACILE_STATE_SALT,
            compress=True,
        )

        try:
            authorization_url = build_dossierfacile_authorization_url(request.user.email, state)
        except ImproperlyConfigured:
            return Response(
                {"detail": "DossierFacile integration is not configured.", "type": "dossierfacile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"authorization_url": authorization_url, "state": state}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Complete DossierFacile link flow",
    description="Exchanges the authorization code and links the DossierFacile account to the authenticated student.",
    request=StudentDossierFacileCompleteConnectSerializer,
    responses={200: StudentDossierFacileStatusSerializer},
)
class StudentDossierFacileCompleteConnectView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentDossierFacileCompleteConnectSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        student = _get_student_or_none(request.user)
        if not student:
            return Response(
                {"detail": "Only student accounts can link DossierFacile.", "type": "not_student"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            state_payload = signing.loads(
                serializer.validated_data["state"],
                salt=DOSSIERFACILE_STATE_SALT,
                max_age=settings.DOSSIERFACILE_STATE_TTL_SECONDS,
            )
        except signing.SignatureExpired:
            return Response(
                {"detail": "Expired DossierFacile state parameter.", "type": "expired_state"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid DossierFacile state parameter.", "type": "invalid_state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if state_payload.get("user_id") != request.user.id:
            return Response(
                {"detail": "Invalid DossierFacile state parameter.", "type": "invalid_state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = exchange_dossierfacile_code_for_token(serializer.validated_data["code"])
            profile = fetch_dossierfacile_tenant_profile(access_token)
        except ImproperlyConfigured:
            return Response(
                {"detail": "DossierFacile integration is not configured.", "type": "dossierfacile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except DossierFacileServiceError as exc:
            return Response({"detail": exc.message, "type": exc.error_type}, status=exc.status_code)

        student.dossierfacile_linked_at = now()
        student.dossierfacile_tenant_id = extract_dossierfacile_tenant_id(profile)
        sharing_data = extract_dossierfacile_sharing_data(profile)
        student.dossierfacile_status = sharing_data["status"]
        student.dossierfacile_url = sharing_data["dossier_url"]
        student.dossierfacile_pdf_url = sharing_data["dossier_pdf_url"]
        student.dossierfacile_last_synced_at = now()
        student.save(
            update_fields=[
                "dossierfacile_linked_at",
                "dossierfacile_tenant_id",
                "dossierfacile_status",
                "dossierfacile_url",
                "dossierfacile_pdf_url",
                "dossierfacile_last_synced_at",
            ]
        )

        return Response(
            {
                "is_linked": True,
                "linked_at": student.dossierfacile_linked_at,
                "tenant_id": student.dossierfacile_tenant_id,
                "dossier_status": student.dossierfacile_status,
                "dossier_url": student.dossierfacile_url,
                "dossier_pdf_url": student.dossierfacile_pdf_url,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Get DossierFacile link status",
    description="Returns the DossierFacile link status for the authenticated student account.",
    responses={200: StudentDossierFacileStatusSerializer},
)
class StudentDossierFacileStatusView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        student = _get_student_or_none(request.user)
        if not student:
            return Response(
                {"detail": "Only student accounts can access this endpoint.", "type": "not_student"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "is_linked": bool(student.dossierfacile_linked_at),
                "linked_at": student.dossierfacile_linked_at,
                "tenant_id": student.dossierfacile_tenant_id,
                "dossier_status": student.dossierfacile_status,
                "dossier_url": student.dossierfacile_url,
                "dossier_pdf_url": student.dossierfacile_pdf_url,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="DossierFacile webhook",
    description="Receives DossierFacile updates and syncs dossier status/URLs for the related student.",
    request=DossierFacileWebhookSerializer,
    responses={200: {"message": "Webhook processed"}},
)
class StudentDossierFacileWebhookView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = DossierFacileWebhookSerializer
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        configured_key = settings.DOSSIERFACILE_WEBHOOK_API_KEY
        if not configured_key:
            return Response(
                {"detail": "DossierFacile webhook is not configured.", "type": "dossierfacile_not_configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        provided_key = request.headers.get("X-Api-Key") or request.headers.get("X-API-KEY")
        if provided_key != configured_key:
            return Response(
                {"detail": "Unauthorized webhook request.", "type": "unauthorized_webhook"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant_id = serializer.validated_data["tenant_id"]

        student = Student.objects.filter(dossierfacile_tenant_id=tenant_id).first()
        if not student:
            return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)

        status_value = serializer.validated_data.get("status")
        status_upper = status_value.upper() if status_value else None

        if status_upper in {"ACCESS_REVOKED", "DELETED_ACCOUNT"}:
            student.dossierfacile_linked_at = None
            student.dossierfacile_status = status_upper
            student.dossierfacile_url = None
            student.dossierfacile_pdf_url = None
        else:
            student.dossierfacile_status = status_value
            student.dossierfacile_url = serializer.validated_data.get("dossierUrl")
            student.dossierfacile_pdf_url = serializer.validated_data.get("dossierPdfUrl")
            if not student.dossierfacile_linked_at:
                student.dossierfacile_linked_at = now()

        student.dossierfacile_last_synced_at = now()
        student.save(
            update_fields=[
                "dossierfacile_linked_at",
                "dossierfacile_status",
                "dossierfacile_url",
                "dossierfacile_pdf_url",
                "dossierfacile_last_synced_at",
            ]
        )

        return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)
