from rest_framework import serializers

from accommodation.filters import AccommodationFilter
from accommodation.models import Accommodation
from .models import AccommodationAlert
from territories.serializers import DepartmentSerializer, AcademySerializer, CitySerializer
from territories.models import City, Department, Academy


class AccommodationAlertSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    academy = AcademySerializer(read_only=True)
    count = serializers.SerializerMethodField()
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
            "count",
        )

    def get_count(self, obj):
        queryset = Accommodation.objects.online_with_availibility_first()
        data = {}
        # filter by department, city or academy
        if obj.department:
            bbox = obj.department.get_bbox()
            if bbox:
                data["bbox"] = f"{bbox['xmin']},{bbox['ymin']},{bbox['xmax']},{bbox['ymax']}"
        elif obj.city:
            bbox = obj.city.get_bbox()
            if bbox:
                data["bbox"] = f"{bbox['xmin']},{bbox['ymin']},{bbox['xmax']},{bbox['ymax']}"
        elif obj.academy_id:
            data["academy_id"] = obj.academy_id

        if obj.has_coliving is True:
            data["has_coliving"] = True
        if obj.is_accessible is True:
            data["is_accessible"] = True
        if obj.max_price is not None:
            data["price_max"] = str(obj.max_price)
        filterset = AccommodationFilter(data=data, queryset=queryset)
        return filterset.qs.count()
