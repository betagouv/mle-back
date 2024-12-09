from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import Accommodation


class AccommodationAdmin(OSMGeoAdmin):
    list_display = (
        "name",
        "residence_type",
        "address",
        "city",
        "postal_code",
        "owner_name",
        "nb_total_apartments",
        "nb_accessible_apartments",
    )
    list_filter = ("residence_type", "city", "postal_code")
    search_fields = ("name", "address", "city")
    ordering = ("name",)


admin.site.register(Accommodation, AccommodationAdmin)
