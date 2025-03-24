import base64

from rest_framework import serializers


class BinaryToBase64Field(serializers.Field):
    def to_representation(self, value):
        if value:
            return f"data:image/jpeg;base64,{base64.b64encode(value).decode('utf-8')}"
        return None

    def to_internal_value(self, data):
        if isinstance(data, bytes):
            return data
        raise serializers.ValidationError("This field is expecting binary data.")
