from django.db.models import Func
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from unidecode import unidecode

from territories.models import Academy, City, Department

from .serializers import TerritoryCombinedSerializer


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
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        query = request.GET.get("q") or None

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
