from django.contrib.gis.geos import Point
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, generics, mixins, permissions, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import AccommodationFilter
from .models import Accommodation, FavoriteAccommodation
from .serializers import (
    AccommodationDetailSerializer,
    AccommodationGeoSerializer,
    FavoriteAccommodationGeoSerializer,
    MyAccommodationGeoSerializer,
)
from .utils import upload_image_to_s3


@extend_schema(
    summary="Retrieve a single published accommodation",
    description="Return detailed information about a published accommodation identified by its slug.",
    responses=AccommodationDetailSerializer,
)
class AccommodationDetailView(generics.RetrieveAPIView):
    queryset = Accommodation.objects.online()
    serializer_class = AccommodationDetailSerializer
    lookup_field = "slug"


@extend_schema(
    summary="List all published accommodations",
    description="Return a list of all published accommodations, supporting filters such as bbox, accessibility, coliving, price, etc.",
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
            description="Return only accommodations with accessible apartments (nb_accessible_apartments > 0).",
            required=False,
        ),
        OpenApiParameter(
            "only_with_availibility",
            OpenApiTypes.BOOL,
            description="Return only accommodations with available apartments (nb_t1_available > 0 | nb_t1_bis_available > 0 | nb_t2_available > 0 | nb_t3_available > 0 | nb_t4_more_available > 0).",
            required=False,
        ),
        OpenApiParameter(
            "has_coliving",
            OpenApiTypes.BOOL,
            description="Return only accommodations offering coliving options (nb_coliving_apartments > 0).",
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
            description="Maximum price (in euros) for filtering accommodations below the given value.",
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


@extend_schema(
    summary="List or create accommodations owned by the authenticated owner",
    description="Allows an authenticated owner to list and create accommodations linked to their owner account.",
    responses=AccommodationGeoSerializer,
    parameters=[
        OpenApiParameter(
            name="has_availability",
            type=OpenApiTypes.BOOL,
            description="Filter accommodations to return only those with available apartments. Use 'true' to enable.",
            required=False,
        ),
        OpenApiParameter(
            "search",
            type=OpenApiTypes.STR,
            description="Search accommodations by name.",
            required=False,
        ),
    ],
)
class MyAccommodationListView(generics.ListCreateAPIView):
    serializer_class = AccommodationGeoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        owners = getattr(self.request.user, "owners", None)
        if not (owners and owners.exists()):
            return Accommodation.objects.none()

        qs = Accommodation.objects.filter(owner__in=self.request.user.owners.all())

        has_availability = self.request.query_params.get("has_availability")
        if has_availability is not None:
            val = has_availability.lower() in ("true", "1", "yes")
            if val:
                qs = qs.filter(
                    Q(nb_t1_available__gt=0)
                    | Q(nb_t1_bis_available__gt=0)
                    | Q(nb_t2_available__gt=0)
                    | Q(nb_t3_available__gt=0)
                    | Q(nb_t4_more_available__gt=0)
                )

        return qs

    @extend_schema(
        summary="Create a new accommodation for the authenticated owner",
        description="Create a new accommodation belonging to the authenticated user’s owner account.",
        request=AccommodationGeoSerializer,
        responses=AccommodationGeoSerializer,
    )
    def perform_create(self, serializer):
        data = self.request.data.copy()
        geom = data.get("geom")
        if geom and isinstance(geom, dict) and geom.get("type") == "Point":
            coordinates = geom.get("coordinates")
            if coordinates:
                data["geom"] = Point(*coordinates)

        # TODO: assuming user can have only one owner, which is the case ATM, except for bizdev
        serializer.save(owner=self.request.user.owners.first(), **data)


@extend_schema(
    summary="Retrieve or update a specific accommodation owned by the authenticated owner",
    description="Allows an authenticated owner to retrieve or partially update an accommodation by slug.",
    request=MyAccommodationGeoSerializer,
    responses=MyAccommodationGeoSerializer,
)
class MyAccommodationDetailView(generics.GenericAPIView):
    serializer_class = MyAccommodationGeoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        owners = getattr(self.request.user, "owners", None)
        if owners and owners.exists():
            return Accommodation.objects.filter(owner__in=owners.all())
        return Accommodation.objects.none()

    def get_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs[self.lookup_field])

    @extend_schema(
        summary="Retrieve an accommodation belonging to the authenticated owner",
        responses=MyAccommodationGeoSerializer,
    )
    def get(self, request, *args, **kwargs):
        accommodation = self.get_object()
        serializer = self.get_serializer(accommodation)
        return Response(serializer.data)

    @extend_schema(
        summary="Partially update an accommodation belonging to the authenticated owner",
        request=MyAccommodationGeoSerializer,
        responses=MyAccommodationGeoSerializer,
    )
    def patch(self, request, *args, **kwargs):
        accommodation = self.get_object()
        serializer = self.get_serializer(accommodation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Upload one or more images for an accommodation, authenticated as owner",
    description=(
        "Upload one or multiple image files (multipart/form-data) for an accommodation "
        "belonging to the authenticated owner. Returns public S3 URLs. "
        "The accommodation is not modified; use PATCH afterwards to save the URLs in order."
    ),
    request={"multipart/form-data": {"images": {"type": "array", "items": {"type": "string", "format": "binary"}}}},
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
)
class MyAccommodationImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        get_object_or_404(
            Accommodation.objects.filter(owner__in=request.user.owners.all()),
            slug=slug,
        )

        files = request.FILES.getlist("images")
        if not files:
            return Response(
                {"detail": "No files provided. Expecting field 'images'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for file_ in files:
            if file_.size > 10 * 1024 * 1024:  # 10MB max
                return Response(
                    {"detail": f"File {file_.name} exceeds the 10MB limit."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        uploaded_urls = [upload_image_to_s3(file_.read()) for file_ in files]

        return Response({"images_urls": uploaded_urls}, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="List user favorite accommodations",
        description=(
            "Returns the list of accommodations marked as favorites by the "
            "authenticated user. Results are automatically filtered based on "
            "`request.user`."
        ),
        responses={
            200: FavoriteAccommodationGeoSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
    create=extend_schema(
        summary="Add a favorite accommodation",
        description=(
            "Adds an accommodation to the authenticated user's list of favorites. "
            "The `accommodation_id` must be provided in the request body. "
            "If the favorite already exists, the API simply returns the existing object."
        ),
        request=FavoriteAccommodationGeoSerializer,
        responses={
            201: FavoriteAccommodationGeoSerializer,
            400: OpenApiResponse(description="Invalid request"),
            401: OpenApiResponse(description="Authentication required"),
        },
        examples=[
            OpenApiExample(
                name="add_favorite_example",
                summary="Add accommodation to favorites",
                value={"accommodation_slug": "my-favorite-accommodation"},
                request_only=True,
            )
        ],
    ),
    destroy=extend_schema(
        summary="Remove a favorite accommodation",
        description=(
            "Deletes a favorite belonging to the authenticated user. "
            "Attempting to delete another user's favorite will return a 404 or 403 "
            "depending on configuration."
        ),
        responses={
            204: OpenApiResponse(description="Favorite deleted"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Favorite not found"),
        },
    ),
)
class FavoriteAccommodationViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = FavoriteAccommodationGeoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FavoriteAccommodation.objects.none()
        return FavoriteAccommodation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        favorite = get_object_or_404(FavoriteAccommodation, user=request.user, accommodation__slug=slug)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
