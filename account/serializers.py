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
        fields = ("email", "first_name", "last_name", "role")

    def get_role(self, obj):
        return "admin" if is_superuser_or_bizdev(obj) else "owner" if is_owner(obj) else "user"


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
        )
        student = Student.objects.create(user=user)
        return student


class StudentRegistrationValidationSerializer(serializers.Serializer):
    validation_token = serializers.CharField()
