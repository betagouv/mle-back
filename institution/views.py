from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics

from institution.filters import EducationalInstitutionFilter
from institution.models import EducationalInstitution
from institution.serializers import EducationalInstitutionGeoSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            "bbox",
            OpenApiTypes.STR,
            description="Bounding box for geographic filtering. Format: xmin,ymin,xmax,ymax.",
            required=False,
        ),
        OpenApiParameter(
            "center",
            OpenApiTypes.STR,
            description="Center point for radius filtering. Format: longitude,latitude.",
            required=False,
        ),
        OpenApiParameter(
            "radius",
            OpenApiTypes.NUMBER,
            description="Radius in kilometers for filtering educational institutions around the center point.",
            required=False,
        ),
    ],
    responses=EducationalInstitutionGeoSerializer,
)
class EducationalInstitutionListView(generics.ListAPIView):
    queryset = EducationalInstitution.objects.exclude(geom__isnull=True)
    serializer_class = EducationalInstitutionGeoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EducationalInstitutionFilter
