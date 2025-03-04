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
        "published",
    )
    list_display_as_owner = ("name", "address", "city", "postal_code", "published")
    list_filter = ("city", "postal_code")
    search_fields = ("name", "address", "city")
    ordering = ("name",)
    fields_as_owner = ("published",)
    list_editable = ("published",)
    list_display_links_as_owner = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        try:
            owner = request.user.owner
            return qs.filter(owner=owner)
        except Owner.DoesNotExist:
            return qs.none()

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            return super().get_list_display_links(request, list_display)
        return self.list_display_links_as_owner

    def get_list_display(self, request):
        if request.user.is_superuser:
            return super().get_list_display(request)
        return self.list_display_as_owner

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fields(request, obj)
        return self.fields_as_owner

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return True


admin.site.register(Accommodation, AccommodationAdmin)
