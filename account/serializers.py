import base64

from rest_framework import serializers

from .models import Owner


class OwnerSerializer(serializers.ModelSerializer):
    image_base64 = serializers.SerializerMethodField()

    class Meta:
        model = Owner
        fields = ("name", "slug", "url", "image_base64")

    def get_image_base64(self, obj):
        if obj.image:
            return f"data:image/jpeg;base64,{base64.b64encode(obj.image).decode('utf-8')}"
        return
