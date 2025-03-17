from rest_framework import serializers

from common.serializers import Base64BinaryField

from .models import Owner


class OwnerSerializer(serializers.ModelSerializer):
    image_base64 = Base64BinaryField(required=False, allow_null=True, source="image")

    class Meta:
        model = Owner
        fields = ("name", "slug", "url", "image_base64")
