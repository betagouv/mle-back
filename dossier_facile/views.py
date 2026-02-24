from django.db import transaction
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

from dossier_facile.event_processor import DossierFacileWebhookEventProcessor
from dossier_facile.models import DossierFacileApplication
from dossier_facile.serializers import ApplicationSerializer, ApplyForHousingSerializer
from dossier_facile.use_cases import apply_for_housing

# Create your views here.


class DossierFacileWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if not request.headers.get("X-Api-Key") == settings.DOSSIERFACILE_WEBHOOK_API_KEY:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        processor = DossierFacileWebhookEventProcessor(request.data)
        processed = processor.process_event()
        if not processed:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class StudentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.student is not None


class OwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.owner is not None


class ApplyForHousingView(APIView):
    authentication_classes = [permissions.IsAuthenticated]
    serializer_class = ApplyForHousingSerializer
    permission_classes = [StudentPermission]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            with transaction.atomic():
                application = apply_for_housing(
                    request.user.student, validated_data["accommodation"], validated_data["appartment_type"]
                )
                return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e), "type": "invalid_data"}, status=status.HTTP_400_BAD_REQUEST)


class ApplicationsPerOwnerListView(ListAPIView):
    authentication_classes = [permissions.IsAuthenticated]
    permission_classes = [OwnerPermission]
    serializer_class = ApplicationSerializer
    queryset = DossierFacileApplication.objects.all()

    def get_queryset(self):
        return self.queryset.filter(accommodation__owner=self.request.user.owners.first())
