from django.contrib.gis.db.models.functions import Distance
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .mixins import BBoxMixin, CityMixin
from .models import Academy, City, Department


class NearbyCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("name", "slug")


class CityDetailSerializer(BBoxMixin, CityMixin):
    nearby_cities = serializers.SerializerMethodField()

    @extend_schema_field(NearbyCitySerializer(many=True))
    def get_nearby_cities(self, obj):
        if not obj.boundary:
            return []
        cities = (
            City.objects.exclude(pk=obj.pk)
            .annotate(distance=Distance("boundary", obj.boundary.centroid))
            .order_by("distance")
        )
        return NearbyCitySerializer(cities[:7], many=True).data

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "postal_codes",
            "epci_code",
            "insee_codes",
            "average_income",
            "average_rent",
            "nb_students",
            "bbox",
            "popular",
            "nearby_cities",
            "nb_apartments",
        )


class CityListSerializer(BBoxMixin, CityMixin):
    class Meta:
        model = City

        fields = (
            "id",
            "name",
            "postal_codes",
            "bbox",
            "popular",
            "nb_apartments",
        )


class DepartmentSerializer(BBoxMixin):
    class Meta:
        model = Department
        fields = ("id", "name", "code", "bbox")


class AcademySerializer(BBoxMixin):
    class Meta:
        model = Academy
        fields = ("id", "name", "bbox")


class TerritorySerializer(serializers.Serializer):
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()

    def to_representation(self, instance):
        if isinstance(instance, City):
            return CityListSerializer(instance).data
        elif isinstance(instance, Department):
            return DepartmentSerializer(instance).data
        elif isinstance(instance, Academy):
            return AcademySerializer(instance).data
        return {}


class TerritoryCombinedSerializer(serializers.Serializer):
    academies = AcademySerializer(many=True)
    departments = DepartmentSerializer(many=True)
    cities = CityListSerializer(many=True)
    cities = CityListSerializer(many=True)


class NewsletterSubscriptionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    territory_type = serializers.ChoiceField(
        choices=[("academy", "Academy"), ("department", "Department"), ("city", "City")]
    )
    territory_name = serializers.CharField()
