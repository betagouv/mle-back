import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.helpers import is_owner, is_superuser_or_bizdev

from .models import Owner

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
