from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from qa.admin import QuestionAnswerInline

from .models import Academy, City, Department


@admin.register(City)
class CityAdmin(OSMGeoAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name", "postal_codes"]


@admin.register(Department)
class DepartmentAdmin(OSMGeoAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name", "code"]


@admin.register(Academy)
class AcademyAdmin(OSMGeoAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name"]
