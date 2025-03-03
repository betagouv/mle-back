from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import Accommodation, Owner


class AccommodationAdmin(OSMGeoAdmin):
    list_display = (
        "name",
        "residence_type",
        "address",
        "city",
        "postal_code",
        "nb_total_apartments",
        "nb_accessible_apartments",
    )
    list_filter = ("residence_type", "city", "postal_code")
    search_fields = ("name", "address", "city")
    ordering = ("name",)
    fields = ("published",)  # only published field by default

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        try:
            owner = request.user.owner
            return qs.filter(owner=owner)
        except Owner.DoesNotExist:
            return qs.none()

    def get_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.is_staff:
            return super().get_fields(request, obj)
        return self.fields

    def has_add_permission(self, request):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return True


admin.site.register(Accommodation, AccommodationAdmin)
