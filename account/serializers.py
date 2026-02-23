import base64

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from account.helpers import is_owner, is_superuser_or_bizdev

from .models import Owner, Student

User = get_user_model()


class OwnerSerializer(serializers.ModelSerializer):
    image_base64 = serializers.SerializerMethodField()

    class Meta:
        model = Owner
        fields = ("name", "slug", "url", "image_base64")

    def get_image_base64(self, obj) -> str:
        if obj.image:
            return f"data:image/jpeg;base64,{base64.b64encode(obj.image).decode('utf-8')}"
        return


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role")

    def get_role(self, obj):
        return "admin" if is_superuser_or_bizdev(obj) else "owner" if is_owner(obj) else "user"


class StudentTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class StudentGetTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class StudentRequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Email already exists")

        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError(e.error_dict)

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            is_active=False,
        )
        student = Student.objects.create(user=user)
        return student


class StudentRegistrationValidationSerializer(serializers.Serializer):
    validation_token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password(value)
        return value


class StudentLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class StudentDossierFacileStartConnectSerializer(serializers.Serializer):
    authorization_url = serializers.URLField()
    state = serializers.CharField()


class StudentDossierFacileCompleteConnectSerializer(serializers.Serializer):
    code = serializers.CharField()
    state = serializers.CharField()


class StudentDossierFacileStatusSerializer(serializers.Serializer):
    is_linked = serializers.BooleanField()
    linked_at = serializers.DateTimeField(allow_null=True)
    tenant_id = serializers.CharField(allow_null=True, allow_blank=True)
    dossier_status = serializers.CharField(allow_null=True, allow_blank=True)
    dossier_url = serializers.URLField(allow_null=True)
    dossier_pdf_url = serializers.URLField(allow_null=True)


class DossierFacileWebhookSerializer(serializers.Serializer):
    onTenantId = serializers.CharField(required=False, allow_blank=False)
    connectedTenantId = serializers.CharField(required=False, allow_blank=False)
    tenantId = serializers.CharField(required=False, allow_blank=False)
    status = serializers.CharField(required=False, allow_blank=True)
    dossierUrl = serializers.URLField(required=False, allow_null=True)
    dossierPdfUrl = serializers.URLField(required=False, allow_null=True)

    def validate(self, attrs):
        tenant_id = attrs.get("onTenantId") or attrs.get("connectedTenantId") or attrs.get("tenantId")
        if not tenant_id:
            raise serializers.ValidationError({"detail": "Missing tenant identifier in webhook payload."})
        attrs["tenant_id"] = tenant_id
        return attrs
