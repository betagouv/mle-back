from django.conf import settings
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django_summernote.widgets import SummernoteWidget

from accommodation.models import Accommodation, ExternalSource


class ExternalSourceInline(admin.TabularInline):
    model = ExternalSource
    extra = 0
    can_delete = False
    readonly_fields = ("source", "source_id")

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description=gettext_lazy("Unpublish selected accommodations"))
def unpublish_accommodations(modeladmin, request, queryset):
    updated_count = queryset.update(published=False)
    modeladmin.message_user(request, f"{updated_count} accommodation(s) have been unpublished.")


@admin.action(description=gettext_lazy("Publish selected accommodations"))
def publish_accommodations(modeladmin, request, queryset):
    updated_count = queryset.update(published=True)
    modeladmin.message_user(request, f"{updated_count} accommodation(s) have been published.")


@admin.action(description=gettext_lazy("Make unavailable selected accommodations"))
def unavailable_accommodations(modeladmin, request, queryset):
    updated_count = queryset.update(available=False)
    modeladmin.message_user(request, f"{updated_count} accommodation(s) have been made unavailable.")


@admin.action(description=gettext_lazy("Make available selected accommodations"))
def available_accommodations(modeladmin, request, queryset):
    updated_count = queryset.update(available=True)
    modeladmin.message_user(request, f"{updated_count} accommodation(s) have been made available.")


class AccommodationAdmin(OSMGeoAdmin):
    inlines = [ExternalSourceInline]
    inlines_as_owner = []
    list_display = (
        "name",
        "residence_type",
        "address",
        "city",
        "postal_code",
        "nb_total_apartments",
        "nb_accessible_apartments",
        "published",
        "available",
    )
    list_display_as_owner = (
        "name",
        "address",
        "city",
        "postal_code",
        "published",
        "available",
        "nb_t1",
        "nb_t1_available",
        "nb_t1_bis",
        "nb_t1_bis_available",
        "nb_t2",
        "nb_t2_available",
        "nb_t3",
        "nb_t3_available",
        "nb_t4_more",
        "nb_t4_more_available",
        "price_min_t1",
        "price_max_t1",
        "price_min_t1_bis",
        "price_max_t1_bis",
        "price_min_t2",
        "price_max_t2",
        "price_min_t3",
        "price_max_t3",
        "price_min_t4_more",
        "price_max_t4_more",
    )
    list_filter = ("owner__name", "city", "postal_code")
    list_filter_as_owner = ("city", "postal_code")
    search_fields = ("name", "address", "city")
    ordering = ("name",)
    fields_as_owner = (
        "available",
        "nb_t1",
        "nb_t1_available",
        "nb_t1_bis",
        "nb_t1_bis_available",
        "nb_t2",
        "nb_t2_available",
        "nb_t3",
        "nb_t3_available",
        "nb_t4_more",
        "nb_t4_more_available",
        "price_min_t1",
        "price_max_t1",
        "price_min_t1_bis",
        "price_max_t1_bis",
        "price_min_t2",
        "price_max_t2",
        "price_min_t3",
        "price_max_t3",
        "price_min_t4_more",
        "price_max_t4_more",
    )
    list_editable = ("available",)
    list_editable_as_owner = (
        "available",
        "nb_t1_available",
        "nb_t1_bis_available",
        "nb_t2_available",
        "nb_t3_available",
        "nb_t4_more_available",
        "price_min_t1",
        "price_max_t1",
        "price_min_t1_bis",
        "price_max_t1_bis",
        "price_min_t2",
        "price_max_t2",
        "price_min_t3",
        "price_max_t3",
        "price_min_t4_more",
        "price_max_t4_more",
    )
    readonly_fields = ("display_images", "owner", "residence_type", "slug", "updated_at")
    readonly_fields_as_owner = (
        "display_images",
        "owner",
        "residence_type",
        "slug",
        "nb_t1",
        "nb_t1_bis",
        "nb_t2",
        "nb_t3",
        "nb_t4_more",
    )
    exclude = ("images_urls", "images_count")
    actions_as_owner = [unavailable_accommodations, available_accommodations]
    actions = [unpublish_accommodations, publish_accommodations, unavailable_accommodations, available_accommodations]
    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }

    def _is_superuser_or_bizdev(self, request):
        return request.user.is_superuser or request.user.groups.filter(name="bizdev").exists()

    def get_readonly_fields(self, request, obj=None):
        if self._is_superuser_or_bizdev(request):
            return self.readonly_fields
        return self.readonly_fields_as_owner

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if self._is_superuser_or_bizdev(request):
            return qs

        owners = getattr(request.user, "owners", None)
        if owners and owners.exists():
            return qs.filter(owner__in=owners.all())

        return qs.none()

    def get_list_filter(self, request):
        if self._is_superuser_or_bizdev(request):
            return super().get_list_filter(request)
        return self.list_filter_as_owner

    def get_list_display(self, request):
        if self._is_superuser_or_bizdev(request):
            return super().get_list_display(request)
        self.list_editable = self.list_editable_as_owner
        return self.list_display_as_owner

    def get_fields(self, request, obj=None):
        if self._is_superuser_or_bizdev(request):
            return super().get_fields(request, obj)
        return self.fields_as_owner

    def get_inlines(self, request, obj=None):
        if self._is_superuser_or_bizdev(request):
            return super().get_inlines(request, obj)
        return self.inlines_as_owner

    def get_actions(self, request):
        actions_list = super().get_actions(request)
        if self._is_superuser_or_bizdev(request):
            return actions_list
        return {
            name: action for name, action in actions_list.items() if name in [a.__name__ for a in self.actions_as_owner]
        }

    def display_images(self, obj):
        if obj.images_urls:
            images_html = "".join(
                f'<img src="{image_url}" width="200" height="150" style="margin:5px;"/>'
                for image_url in obj.images_urls
            )
            return format_html(images_html)
        return "No images available"

    display_images.short_description = "Images"

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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}

        obj = self.get_object(request, object_id)
        if obj:
            extra_context["api_url"] = obj.get_absolute_detail_api_url()
            extra_context["superuser_or_contentwriter"] = self._is_superuser_or_bizdev(request)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    change_form_template = "admin/change_form.html"


admin.site.site_title = f"Administration de {settings.SITE_NAME}"
admin.site.site_header = f"Administration de {settings.SITE_NAME}"
admin.site.index_title = f"Bienvenue sur l'administration de {settings.SITE_NAME}"
admin.site.site_url = settings.FRONT_SITE_URL

admin.site.register(Accommodation, AccommodationAdmin)
