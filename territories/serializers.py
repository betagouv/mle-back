from accommodation.models import Accommodation
from django.contrib.gis.db.models.functions import Distance
from rest_framework import serializers

from .mixins import BBoxMixin
from .models import Academy, City, Department


class NearbyCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("name", "slug")


class CityDetailSerializer(BBoxMixin):
    nearby_cities = serializers.SerializerMethodField()
    nb_accommodations = serializers.SerializerMethodField()

    def get_nearby_cities(self, obj):
        if not obj.boundary:
            return []
        cities = (
            City.objects.exclude(pk=obj.pk)
            .annotate(distance=Distance("boundary", obj.boundary.centroid))
            .order_by("distance")
        )
        return NearbyCitySerializer(cities[:7], many=True).data

    def get_nb_accommodations(self, obj):
        return Accommodation.objects.filter(city=obj.name, postal_code__in=obj.postal_codes).count()

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
            "nb_accommodations",
        )


class CityListSerializer(BBoxMixin):
    nb_accommodations = serializers.SerializerMethodField()

    def get_nb_accommodations(self, obj):
        return Accommodation.objects.filter(city=obj.name, postal_code__in=obj.postal_codes).count()

    class Meta:
        model = City

        fields = (
            "id",
            "name",
            "postal_codes",
            "bbox",
            "popular",
            "nb_accommodations",
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
