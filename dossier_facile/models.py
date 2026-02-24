from django.db import models
from accommodation.models import Accommodation
from account.models import Student


# Create your models here.
class DossierFacileTenant(models.Model):
    class DossierFacileTenantStatus(models.TextChoices):
        ACTIVE = "active"
        INACTIVE = "inactive"
        ACCESS_REVOKED = "access_revoked"
        DENIED = "denied"
        VERIFIED = "verified"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="dossier_facile_tenants")
    tenant_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=64, null=True, blank=True, choices=DossierFacileTenantStatus.choices)
    url = models.URLField(max_length=500, null=True, blank=True)
    pdf_url = models.URLField(max_length=500, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class DossierFacileApplication(models.Model):
    tenant = models.ForeignKey(DossierFacileTenant, on_delete=models.CASCADE, related_name="applications")
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, related_name="dossier_facile_applications"
    )
    appartment_type = models.CharField(
        choices=Accommodation.APARTMENT_TYPE_CHOICES.choices,
        max_length=10,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
