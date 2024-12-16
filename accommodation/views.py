from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics

from .filters import AccommodationFilter
from .models import Accommodation
from .serializers import AccommodationDetailSerializer, AccommodationGeoSerializer


@extend_schema(
    responses=AccommodationDetailSerializer,
)
class AccommodationDetailView(generics.RetrieveAPIView):
    queryset = Accommodation.objects.online()
    serializer_class = AccommodationDetailSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            "bbox",
            OpenApiTypes.STR,
            description="Bounding box for geographic filtering. Format: xmin,ymin,xmax,ymax.",
            required=False,
        ),
        OpenApiParameter(
            "is_accessible",
            OpenApiTypes.BOOL,
            description="Filter to return only accommodations with accessible apartments (nb_accessible_apartments > 0).",
            required=False,
        ),
    ],
    responses=AccommodationGeoSerializer,
)
class AccommodationListView(generics.ListAPIView):
    queryset = Accommodation.objects.online()
    serializer_class = AccommodationGeoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AccommodationFilter
