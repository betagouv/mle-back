from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accommodation.models import Accommodation


class BBoxMixin(serializers.ModelSerializer):
    bbox = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.DictField(
            child=serializers.FloatField(), help_text="Bounding box with xmin, ymin, xmax, ymax coordinates"
        )
    )
    def get_bbox(self, obj):
        return obj.get_bbox()


class CityMixin(serializers.ModelSerializer):
    nb_apartments = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField(help_text="Number of accommodations in the city"))
    def get_nb_apartments(self, obj):
        return (
            Accommodation.objects.filter(city=obj.name, postal_code__in=obj.postal_codes).aggregate(
                total=Sum("nb_total_apartments")
            )["total"]
            or 0
        )
