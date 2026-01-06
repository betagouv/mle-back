import logging
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from django.db import transaction
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError

from account.throttles import PasswordResetThrottle
from notifications.exceptions import EmailDeliveryError

from .models import Owner, StudentRegistrationToken
from .serializers import (
    OwnerSerializer,
    PasswordResetConfirmSerializer,
    StudentLogoutSerializer,
    StudentRegistrationValidationSerializer,
    StudentRequestPasswordResetSerializer,
    StudentTokenResponseSerializer,
    StudentGetTokenSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from .serializers import StudentRegistrationSerializer
from .services import request_password_reset
from account.serializers import UserSerializer

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str

from drf_spectacular.utils import OpenApiResponse

from notifications.factories import get_email_gateway
from notifications.services import send_account_validation

User = get_user_model()
logger = logging.getLogger(__name__)


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
