from django.contrib import admin

from dossier_facile.models import DossierFacileApplication, DossierFacileOAuthState, DossierFacileTenant


@admin.register(DossierFacileTenant)
class DossierFacileTenantAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "tenant_id", "status", "last_synced_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("tenant_id", "name", "student__user__email", "student__user__username")
    raw_id_fields = ("student",)


@admin.register(DossierFacileOAuthState)
class DossierFacileOAuthStateAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "state", "expires_at", "created_at")
    search_fields = ("state", "user__email", "user__username")
    raw_id_fields = ("user",)


@admin.register(DossierFacileApplication)
class DossierFacileApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "accommodation", "appartment_type", "created_at")
    raw_id_fields = ("tenant", "accommodation")
