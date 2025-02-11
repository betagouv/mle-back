from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class BBoxMixin(serializers.ModelSerializer):
    bbox = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.DictField(
            child=serializers.FloatField(), help_text="Bounding box with xmin, ymin, xmax, ymax coordinates"
        )
    )
    def get_bbox(self, obj):
        return obj.get_bbox()
