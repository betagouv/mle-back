import base64

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy

from .forms import OwnerAdminForm
from .models import Owner


class OwnerUsersInline(admin.TabularInline):
    model = Owner.users.through
    extra = 1
    verbose_name = gettext_lazy("Linked user")
    verbose_name_plural = gettext_lazy("Linked users")
    autocomplete_fields = ["user"]


class OwnerAdmin(admin.ModelAdmin):
    form = OwnerAdminForm
    list_display = ("name", "image_preview", "list_users")
    readonly_fields = ("image_preview",)
    search_fields = ("name", "users__email")
    filter_horizontal = ("users",)
    inlines = [OwnerUsersInline]
    exclude = ("users",)

    def image_preview(self, obj):
        if obj.image:
            image_base64 = base64.b64encode(obj.image).decode("utf-8")
            return format_html(f'<img src="data:image/png;base64,{image_base64}" width="100" height="45"/>')
        return "No Image"

    image_preview.short_description = "Image"

    def list_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()]) or "—"

    list_users.short_description = gettext_lazy("Linked users")


admin.site.register(Owner, OwnerAdmin)
