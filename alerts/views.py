from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets, permissions
from .models import AccommodationAlert
from .serializers import AccommodationAlertSerializer


@extend_schema(
    summary="List all accommodation alerts",
    description="Return a list of all accommodation alerts",
    parameters=[
        OpenApiParameter(
            name="city_id",
            description="The ID of the city",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="department_id",
            description="The ID of the department",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="academy_id",
            description="The ID of the academy",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="has_coliving",
            description="Whether the alert has coliving",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="is_accessible",
            description="Whether the alert is accessible",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="max_price",
            description="The maximum price of the alert",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="receive_notifications",
            description="Whether the alert should receive notifications",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="name",
            description="The name of the alert",
            required=False,
            type=str,
        ),
    ],
    responses=AccommodationAlertSerializer,
)
class AccommodationAlertViewSet(viewsets.ModelViewSet):
    queryset = AccommodationAlert.objects.all()
    serializer_class = AccommodationAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(student=self.request.user.student)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student)
