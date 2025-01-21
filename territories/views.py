from django.db.models import Func
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from unidecode import unidecode

from territories.models import Academy, City, Department
from territories.serializers import CityDetailSerializer

from .serializers import AcademySerializer, CityListSerializer, DepartmentSerializer, TerritoryCombinedSerializer


class Unaccent(Func):
    function = "unaccent"
    template = "%(function)s(%(expressions)s)"


class TerritoryCombinedListAPIView(APIView):
    serializer_class = TerritoryCombinedSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Term to filter academies, departments, and cities by name (case-insensitive, accent-insensitive).",
                required=True,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        query = request.GET["q"]

        academies = Academy.objects.all()
        departments = Department.objects.all()
        cities = City.objects.all()

        if query:
            query = unidecode(query)
            academies = Academy.objects.annotate(name_unaccent=Unaccent("name")).filter(name_unaccent__icontains=query)

            departments = Department.objects.annotate(name_unaccent=Unaccent("name")).filter(
                name_unaccent__icontains=query
            )

            cities = City.objects.annotate(name_unaccent=Unaccent("name")).filter(name_unaccent__icontains=query)

        data = {
            "academies": academies,
            "departments": departments,
            "cities": cities,
        }

        serializer = TerritoryCombinedSerializer(data)
        return Response(serializer.data)


class AcademyListAPIView(APIView):
    serializer_class = AcademySerializer

    def get(self, request, *args, **kwargs):
        academies = Academy.objects.all().order_by("name")

        serializer = AcademySerializer(academies, many=True)
        return Response(serializer.data)


class DepartmentListAPIView(APIView):
    serializer_class = DepartmentSerializer

    def get(self, request, *args, **kwargs):
        departments = Department.objects.all().order_by("name")

        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class CityListAPIView(APIView):
    serializer_class = CityListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="department",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Department code to filter cities (for example: 75).",
                required=False,
            ),
            OpenApiParameter(
                name="popular",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter popular cities. Use true/false.",
                required=False,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        cities = City.objects.all()

        if department := (request.GET.get("department") or None):
            cities = cities.filter(department__code=department)

        if popular := (request.GET.get("popular") or None):
            if popular.lower() == "true":
                cities = cities.filter(popular=True)
            elif popular.lower() == "false":
                cities = cities.filter(popular=False)

        cities.order_by("name")
        serializer = CityListSerializer(cities, many=True)
        return Response(serializer.data)
        return Response(serializer.data)


class CityDetailView(RetrieveAPIView):
    queryset = City.objects.all()
    serializer_class = CityDetailSerializer
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get(self.lookup_field)
        return get_object_or_404(self.queryset, slug=slug)
