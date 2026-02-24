from rest_framework import serializers

from accommodation.models import Accommodation
from account.serializers import StudentSerializer
from dossier_facile.models import DossierFacileApplication, DossierFacileTenant


class ApplyForHousingSerializer(serializers.Serializer):
    accommodation = serializers.PrimaryKeyRelatedField(queryset=Accommodation.objects.all())
    appartment_type = serializers.ChoiceField(choices=Accommodation.APARTMENT_TYPE_CHOICES)


class TenantSerializer(serializers.ModelSerializer):
    student = StudentSerializer()

    class Meta:
        model = DossierFacileTenant
        fields = ("id", "student", "name", "created_at", "updated_at")


class ApplicationSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer()

    class Meta:
        model = DossierFacileApplication
        fields = ("id", "tenant", "accommodation", "appartment_type", "created_at", "updated_at")
