from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from qa.admin import QuestionAnswerInline

from .models import Academy, City, Country, Department


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    inlines = (QuestionAnswerInline,)
    search_fields = ("name",)


@admin.register(City)
class CityAdmin(OSMGeoAdmin):
    inlines = (QuestionAnswerInline,)
    readonly_fields = ("insee_code",)
    search_fields = ("name", "postal_codes", "insee_code")


@admin.register(Department)
class DepartmentAdmin(OSMGeoAdmin):
    inlines = (QuestionAnswerInline,)
    search_fields = ("name", "code")


@admin.register(Academy)
class AcademyAdmin(OSMGeoAdmin):
    inlines = (QuestionAnswerInline,)
    search_fields = ("name",)
