from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from institution.models import EducationalInstitution


class EducationalInstitutionAdmin(OSMGeoAdmin):
    list_display = (
        "name",
        "address",
        "city",
        "postal_code",
    )


admin.site.register(EducationalInstitution, EducationalInstitutionAdmin)
