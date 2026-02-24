from typing import Protocol
from dossier_facile.models import DossierFacileTenant, DossierFacileApplication


class DossierFacileEventRule(Protocol):
    def __init__(self, event: dict):
        self.event = event

    def matches(self, event: dict):
        return False

    def handle(self, event: dict):
        pass


class DeletedAccountRule(DossierFacileEventRule):
    def matches(self, event: dict):
        return event.get("partnerCallBackType") == "DELETED_ACCOUNT"

    def handle(self, event: dict):
        # delete the tenant and the application
        DossierFacileTenant.objects.filter(tenant_id=event.get("tenantId")).delete()
        DossierFacileApplication.objects.filter(tenant_id=event.get("tenantId")).delete()


class AccessRevokedRule(DossierFacileEventRule):
    def matches(self, event: dict):
        return event.get("partnerCallBackType") == "ACCESS_REVOKED"

    def handle(self, event: dict):
        # revoke the access to the tenant and the application
        DossierFacileTenant.objects.filter(tenant_id=event.get("tenantId")).update(status="access_revoked")
        DossierFacileApplication.objects.filter(tenant_id=event.get("tenantId")).update(status="access_revoked")


class VerifiedAccountRule(DossierFacileEventRule):
    def matches(self, event: dict):
        return event.get("partnerCallBackType") == "VERIFIED_ACCOUNT"

    def handle(self, event: dict):
        # grant the access to the tenant and the application
        DossierFacileTenant.objects.filter(tenant_id=event.get("tenantId")).update(status="verified")


class DeniedAccountRule(DossierFacileEventRule):
    def matches(self, event: dict):
        return event.get("partnerCallBackType") == "DENIED_ACCOUNT"

    def handle(self, event: dict):
        # refuse the access to the tenant and the application
        DossierFacileTenant.objects.filter(tenant_id=event.get("tenantId")).update(status="denied")
        DossierFacileApplication.objects.filter(tenant_id=event.get("tenantId")).delete()


RULES = [DeletedAccountRule, AccessRevokedRule, VerifiedAccountRule, DeniedAccountRule]
