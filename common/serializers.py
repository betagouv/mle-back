import base64

from rest_framework import serializers


class Base64BinaryField(serializers.Field):
    def to_representation(self, value):
        if value:
            return base64.b64encode(value).decode("utf-8")
        return

    def to_internal_value(self, data):
        if data:
            try:
                return base64.b64decode(data)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Invalid base64 data.")
        return
