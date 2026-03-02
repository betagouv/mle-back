from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accommodation.models import Accommodation
from dossier_facile.event_processor import DossierFacileWebhookEventProcessor
from dossier_facile.models import DossierFacileApplication, DossierFacileTenant
from dossier_facile.rules import AccessRevokedRule, DeletedAccountRule, DeniedAccountRule, VerifiedAccountRule
from tests.accommodation.factories import AccommodationFactory
from tests.account.factories import StudentFactory


class DossierFacileTestMixin:
    def create_tenant_with_application(
        self, tenant_id="tenant-123", status_value=DossierFacileTenant.DossierFacileTenantStatus.ACTIVE
    ):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False)
        tenant = DossierFacileTenant.objects.create(
            student=student,
            tenant_id=tenant_id,
            name="Jane Doe",
            status=status_value,
            url=f"https://dfc.example/dossier/{tenant_id}",
            pdf_url=f"https://dfc.example/dossier/{tenant_id}.pdf",
        )
        accommodation = AccommodationFactory()
        application = DossierFacileApplication.objects.create(
            tenant=tenant,
            accommodation=accommodation,
            appartment_type=Accommodation.APARTMENT_TYPE_CHOICES.T1,
        )
        return student, tenant, accommodation, application


@override_settings(DOSSIERFACILE_WEBHOOK_API_KEY="webhook-secret")
class DossierFacileWebhookAPITests(DossierFacileTestMixin, APITestCase):
    def setUp(self):
        self.url = reverse("dossier-facile-webhook")

    def test_webhook_updates_verified_tenant(self):
        _student, tenant, _accommodation, _application = self.create_tenant_with_application()

        response = self.client.post(
            self.url,
            {"partnerCallBackType": "VERIFIED_ACCOUNT", "tenantId": tenant.tenant_id},
            format="json",
            HTTP_X_API_KEY="webhook-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.VERIFIED)

    def test_webhook_rejects_invalid_api_key(self):
        response = self.client.post(
            self.url,
            {"partnerCallBackType": "VERIFIED_ACCOUNT", "tenantId": "tenant-123"},
            format="json",
            HTTP_X_API_KEY="wrong-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DossierFacileRulesTests(DossierFacileTestMixin, TestCase):
    def test_deleted_account_rule_deletes_tenant_and_related_applications(self):
        _student, tenant, _accommodation, application = self.create_tenant_with_application()

        rule = DeletedAccountRule({"partnerCallBackType": "DELETED_ACCOUNT", "tenantId": tenant.tenant_id})
        rule.handle({"partnerCallBackType": "DELETED_ACCOUNT", "tenantId": tenant.tenant_id})

        self.assertFalse(DossierFacileTenant.objects.filter(pk=tenant.pk).exists())
        self.assertFalse(DossierFacileApplication.objects.filter(pk=application.pk).exists())

    def test_access_revoked_rule_updates_tenant_and_keeps_application(self):
        _student, tenant, _accommodation, application = self.create_tenant_with_application()

        rule = AccessRevokedRule({"partnerCallBackType": "ACCESS_REVOKED", "tenantId": tenant.tenant_id})
        rule.handle({"partnerCallBackType": "ACCESS_REVOKED", "tenantId": tenant.tenant_id})

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.ACCESS_REVOKED)
        self.assertTrue(DossierFacileApplication.objects.filter(pk=application.pk).exists())

    def test_verified_account_rule_updates_tenant_status(self):
        _student, tenant, _accommodation, _application = self.create_tenant_with_application(
            status_value=DossierFacileTenant.DossierFacileTenantStatus.INACTIVE
        )

        rule = VerifiedAccountRule({"partnerCallBackType": "VERIFIED_ACCOUNT", "tenantId": tenant.tenant_id})
        rule.handle({"partnerCallBackType": "VERIFIED_ACCOUNT", "tenantId": tenant.tenant_id})

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.VERIFIED)

    def test_denied_account_rule_updates_tenant_and_deletes_related_applications(self):
        _student, tenant, _accommodation, application = self.create_tenant_with_application()

        rule = DeniedAccountRule({"partnerCallBackType": "DENIED_ACCOUNT", "tenantId": tenant.tenant_id})
        rule.handle({"partnerCallBackType": "DENIED_ACCOUNT", "tenantId": tenant.tenant_id})

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.DENIED)
        self.assertFalse(DossierFacileApplication.objects.filter(pk=application.pk).exists())


class DossierFacileEventProcessorTests(DossierFacileTestMixin, TestCase):
    def test_process_event_without_argument_uses_instance_event_and_dispatches_rule(self):
        _student, tenant, _accommodation, _application = self.create_tenant_with_application(
            status_value=DossierFacileTenant.DossierFacileTenantStatus.INACTIVE
        )

        processor = DossierFacileWebhookEventProcessor(
            {"partnerCallBackType": "VERIFIED_ACCOUNT", "tenantId": tenant.tenant_id}
        )

        processed = processor.process_event()

        self.assertTrue(processed)
        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.VERIFIED)

    def test_process_event_returns_false_when_no_rule_matches(self):
        _student, tenant, _accommodation, _application = self.create_tenant_with_application()

        processor = DossierFacileWebhookEventProcessor(
            {"partnerCallBackType": "UNKNOWN_EVENT", "tenantId": tenant.tenant_id}
        )

        processed = processor.process_event()

        self.assertFalse(processed)
        tenant.refresh_from_db()
        self.assertEqual(tenant.status, DossierFacileTenant.DossierFacileTenantStatus.ACTIVE)
