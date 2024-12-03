from rest_framework.response import Response
from rest_framework.views import APIView

from territories.models import Academy, City, Department

from .serializers import TerritoryCombinedSerializer


class TerritoryCombinedListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        data = {
            "academies": Academy.objects.all(),
            "departments": Department.objects.all(),
            "cities": City.objects.all(),
        }

        serializer = TerritoryCombinedSerializer(data)
        return Response(serializer.data)
