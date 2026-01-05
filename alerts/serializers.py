from rest_framework import serializers
from .models import AccommodationAlert
from territories.serializers import DepartmentSerializer, AcademySerializer, CitySerializer
from territories.models import City, Department, Academy


class AccommodationAlertSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    academy = AcademySerializer(read_only=True)
    # WRITE
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source="city",
        write_only=True,
        required=False,
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
        required=False,
    )
    academy_id = serializers.PrimaryKeyRelatedField(
        queryset=Academy.objects.all(),
        source="academy",
        write_only=True,
        required=False,
    )

    class Meta:
        model = AccommodationAlert
        fields = (
            "id",
            "name",
            "city",
            "city_id",
            "department",
            "department_id",
            "academy",
            "academy_id",
            "has_coliving",
            "is_accessible",
            "max_price",
        )
