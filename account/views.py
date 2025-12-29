from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from django.db import transaction
from django.conf import settings

from .models import Owner, StudentRegistrationToken
from .serializers import OwnerSerializer, StudentRegistrationValidationSerializer

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from .serializers import StudentRegistrationSerializer
from .services import send_student_registration_email


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

        send_student_registration_email(student, validation_link)
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
