import base64

from django.contrib import admin
from django.utils.html import format_html

from .forms import OwnerAdminForm
from .models import Owner


class OwnerAdmin(admin.ModelAdmin):
    form = OwnerAdminForm
    list_display = ("name", "image_preview")
    readonly_fields = ("image_preview",)
    search_fields = ("name",)

    def image_preview(self, obj):
        if obj.image:
            image_base64 = base64.b64encode(obj.image).decode("utf-8")
            return format_html(f'<img src="data:image/png;base64,{image_base64}" width="100" height="45"/>')
        return "No Image"

    image_preview.short_description = "Image"


admin.site.register(Owner, OwnerAdmin)
