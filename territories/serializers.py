from rest_framework import serializers

from .models import Academy, City, Department


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "postal_codes"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class AcademySerializer(serializers.ModelSerializer):
    class Meta:
        model = Academy
        fields = ["id", "name"]


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
