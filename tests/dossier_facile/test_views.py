from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from accommodation.models import Accommodation
from dossier_facile.models import DossierFacileApplication, DossierFacileTenant
from dossier_facile.views import ApplicationsPerOwnerListView, ApplyForHousingView
from tests.account.factories import OwnerFactory, StudentFactory
from tests.accommodation.factories import AccommodationFactory


class DossierFacileViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user_model = get_user_model()

    def test_apply_for_housing_creates_application_for_verified_student(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
            url="https://example.com/dossier",
            pdf_url="https://example.com/dossier.pdf",
        )
        accommodation = AccommodationFactory(nb_t1=1)

        request = self.factory.post(
            "/api/dossier-facile/apply/",
            {
                "accommodation": accommodation.pk,
                "appartment_type": Accommodation.APARTMENT_TYPE_CHOICES.T1,
            },
            format="json",
        )
        force_authenticate(request, user=student.user)

        response = ApplyForHousingView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DossierFacileApplication.objects.count(), 1)
        application = DossierFacileApplication.objects.get()
        self.assertEqual(application.tenant.tenant_id, "tenant-123")
        self.assertEqual(application.accommodation_id, accommodation.pk)
        self.assertEqual(response.data["appartment_type"], Accommodation.APARTMENT_TYPE_CHOICES.T1)

    def test_apply_for_housing_rejects_non_student(self):
        user = self.user_model.objects.create_user(
            username="plain-user",
            email="plain@example.com",
            password="testpassword123",
            is_active=True,
        )
        accommodation = AccommodationFactory(nb_t1=1)

        request = self.factory.post(
            "/api/dossier-facile/apply/",
            {
                "accommodation": accommodation.pk,
                "appartment_type": Accommodation.APARTMENT_TYPE_CHOICES.T1,
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = ApplyForHousingView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_list_only_their_dossier_facile_applications(self):
        owner_user = self.user_model.objects.create_user(
            username="owner-user",
            email="owner@example.com",
            password="testpassword123",
            is_active=True,
        )
        owner = OwnerFactory(users=[owner_user])
        other_owner = OwnerFactory()
        accommodation = AccommodationFactory(owner=owner)
        other_accommodation = AccommodationFactory(owner=other_owner)

        student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        )
        other_student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        other_tenant = DossierFacileTenant.objects.create(
            student=other_student,
            tenant_id="tenant-456",
            name="John Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        )
        DossierFacileApplication.objects.create(
            tenant=tenant,
            accommodation=accommodation,
            appartment_type=Accommodation.APARTMENT_TYPE_CHOICES.T1,
        )
        DossierFacileApplication.objects.create(
            tenant=other_tenant,
            accommodation=other_accommodation,
            appartment_type=Accommodation.APARTMENT_TYPE_CHOICES.T2,
        )

        request = self.factory.get("/api/dossier-facile/applications/")
        force_authenticate(request, user=owner_user)

        response = ApplicationsPerOwnerListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["accommodation"], accommodation.pk)

    def test_applications_list_rejects_non_owner(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False)

        request = self.factory.get("/api/dossier-facile/applications/")
        force_authenticate(request, user=student.user)

        response = ApplicationsPerOwnerListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DossierFacileViewsURLTests(APITestCase):
    def test_apply_for_housing_url_happy_path(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
            url="https://example.com/dossier",
            pdf_url="https://example.com/dossier.pdf",
        )
        accommodation = AccommodationFactory(nb_t1=1)
        self.client.force_authenticate(user=student.user)

        response = self.client.post(
            reverse("dossier-facile-apply-for-housing"),
            {
                "accommodation": accommodation.pk,
                "appartment_type": Accommodation.APARTMENT_TYPE_CHOICES.T1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DossierFacileApplication.objects.count(), 1)
        self.assertEqual(response.json()["accommodation"], accommodation.pk)
        self.assertEqual(response.json()["appartment_type"], Accommodation.APARTMENT_TYPE_CHOICES.T1)

    def test_applications_per_owner_url_happy_path(self):
        owner_user = get_user_model().objects.create_user(
            username="owner-user-url",
            email="owner-url@example.com",
            password="testpassword123",
            is_active=True,
        )
        owner = OwnerFactory(users=[owner_user])
        other_owner = OwnerFactory()
        accommodation = AccommodationFactory(owner=owner)
        other_accommodation = AccommodationFactory(owner=other_owner)

        student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id="tenant-123",
            name="Jane Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        )
        other_student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        other_tenant = DossierFacileTenant.objects.create(
            student=other_student,
            tenant_id="tenant-456",
            name="John Doe",
            status=DossierFacileTenant.DossierFacileTenantStatus.VERIFIED,
        )
        DossierFacileApplication.objects.create(
            tenant=tenant,
            accommodation=accommodation,
            appartment_type=Accommodation.APARTMENT_TYPE_CHOICES.T1,
        )
        DossierFacileApplication.objects.create(
            tenant=other_tenant,
            accommodation=other_accommodation,
            appartment_type=Accommodation.APARTMENT_TYPE_CHOICES.T2,
        )
        self.client.force_authenticate(user=owner_user)

        response = self.client.get(reverse("dossier-facile-applications-per-owner"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["accommodation"], accommodation.pk)
