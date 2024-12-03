from rest_framework.response import Response
from rest_framework.views import APIView

from territories.models import Academy, City, Department

from .serializers import AcademySerializer, CitySerializer, DepartmentSerializer


class TerritoryCombinedListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        academies = Academy.objects.all()
        departments = Department.objects.all()
        cities = City.objects.all()

        academy_serializer = AcademySerializer(academies, many=True)
        department_serializer = DepartmentSerializer(departments, many=True)
        city_serializer = CitySerializer(cities, many=True)

        data = {
            "academies": academy_serializer.data,
            "departments": department_serializer.data,
            "cities": city_serializer.data,
        }

        return Response(data)
