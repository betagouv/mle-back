import base64

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.utils.html import format_html

from accommodation.models import Accommodation, ExternalSource
from account.models import Owner


class ExternalSourceInline(admin.TabularInline):
    model = ExternalSource
    extra = 0
    can_delete = False
    readonly_fields = ("source", "source_id")

    def has_add_permission(self, request, obj=None):
        return False


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
    inlines = [ExternalSourceInline]
    inlines_as_owner = []
    list_display_as_owner = ("name", "address", "city", "postal_code", "published")
    list_filter = ("city", "postal_code")
    search_fields = ("name", "address", "city")
    ordering = ("name",)
    fields_as_owner = ("published",)
    list_editable = ("published",)
    list_display_links_as_owner = None
    readonly_fields = (
        "display_images",
        "owner",
        "residence_type",
    )
    exclude = ("images",)

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

    def get_inlines(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_inlines(request, obj)
        return self.inlines_as_owner

    def display_images(self, obj):
        if obj.images:
            images_html = "".join(
                f'<img src="data:image/jpeg;base64,{base64.b64encode(image).decode()}" width="200" height="150" style="margin:5px;"/>'
                for image in obj.images
            )
            return format_html(images_html)
        return "No images available"

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

    display_images.short_description = "Images"


admin.site.register(Accommodation, AccommodationAdmin)
