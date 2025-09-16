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
    lookup_field = "slug"


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
        OpenApiParameter(
            "is_available",
            OpenApiTypes.BOOL,
            description="Filter to return only accommodations with available apartments (nb_t1_available > 0 or nb_t1_bis_available > 0 or nb_t2_available > 0 or nb_t3_available > 0 or nb_t4_more_available > 0).",
            required=False,
        ),
        OpenApiParameter(
            "has_coliving",
            OpenApiTypes.BOOL,
            description="Filter to return only accommodations with coliving apartments (nb_coliving_apartments > 0).",
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
            description="Radius in kilometers for filtering accommodations around the center point.",
            required=False,
        ),
        OpenApiParameter(
            "price_max",
            OpenApiTypes.NUMBER,
            description="Price max in euros for filtering accommodations with a price lower than the given value.",
            required=False,
        ),
    ],
    responses=AccommodationGeoSerializer,
)
class AccommodationListView(generics.ListAPIView):
    queryset = Accommodation.objects.online_with_availibility_first()
    serializer_class = AccommodationGeoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AccommodationFilter
