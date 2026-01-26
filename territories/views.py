from django.db.models import Func, F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from territories.models import Academy, City, Department
from territories.serializers import CityDetailSerializer, NewsletterSubscriptionSerializer
from territories.services import sync_newsletter_subscription_to_brevo
from territories.search import build_combined_territory_queryset
from .serializers import AcademySerializer, CityListSerializer, DepartmentSerializer, TerritoryCombinedSerializer


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
        raw_query = request.GET["q"]

        combined_queryset = build_combined_territory_queryset(raw_query)
        data = {
            "academies": combined_queryset["academies"],
            "departments": combined_queryset["departments"],
            "cities": combined_queryset["cities"],
        }

        serializer = TerritoryCombinedSerializer(data)
        return Response(serializer.data)


class AcademyListAPIView(APIView):
    serializer_class = AcademySerializer

    def get(self, request, *args, **kwargs):
        academies = Academy.objects.annotate(name_unaccent=Func(F("name"), function="unaccent")).order_by(
            "name_unaccent"
        )

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


class CityDetailView(RetrieveAPIView):
    queryset = City.objects.all()
    serializer_class = CityDetailSerializer
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get(self.lookup_field)
        return get_object_or_404(self.queryset, slug=slug)


class NewsletterSubscriptionAPIView(APIView):
    @extend_schema(
        request=NewsletterSubscriptionSerializer,
        responses={201: {"message": "Subscription successful", "email": "string", "territory": "string"}},
        examples=[
            OpenApiExample(
                "Example Request",
                summary="Example request",
                description="Example of a newsletter subscription request with an email and a territory.",
                value={"email": "test@example.com", "territory_type": "city", "territory_name": "Lyon"},
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = NewsletterSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            territory_type = serializer.validated_data["territory_type"]
            territory_name = serializer.validated_data["territory_name"]
            kind = serializer.validated_data["kind"]

            model_map = {
                "academy": Academy,
                "department": Department,
                "city": City,
            }

            model = model_map.get(territory_type)
            territory = get_object_or_404(model, name=territory_name)

            sync_newsletter_subscription_to_brevo(email, territory_type, territory_name, kind)

            return Response(
                {"message": "Subscription successful", "email": email, "territory": territory.name},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
