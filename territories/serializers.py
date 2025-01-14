from rest_framework import serializers

from .mixins import BBoxMixin
from .models import Academy, City, Department


class CitySerializer(BBoxMixin):
    class Meta:
        model = City
        fields = ("id", "name", "postal_codes", "bbox", "average_income")


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
            return CitySerializer(instance).data
        elif isinstance(instance, Department):
            return DepartmentSerializer(instance).data
        elif isinstance(instance, Academy):
            return AcademySerializer(instance).data
        return {}


class TerritoryCombinedSerializer(serializers.Serializer):
    academies = AcademySerializer(many=True)
    departments = DepartmentSerializer(many=True)
    cities = CitySerializer(many=True)
