from rest_framework import serializers


class BBoxMixin(serializers.ModelSerializer):
    bbox = serializers.SerializerMethodField()

    def get_bbox(self, obj):
        return obj.get_bbox()
