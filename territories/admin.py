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
    readonly_fields = ("population", "insee_codes", "epci_code", "average_income", "average_rent", "nb_students")
    search_fields = ("name", "postal_codes", "insee_codes")
    list_filter = ("popular",)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}

        obj = self.get_object(request, object_id)
        if obj:
            extra_context["api_url"] = obj.get_absolute_detail_api_url()

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    change_form_template = "admin/change_form.html"


@admin.register(Department)
class DepartmentAdmin(OSMGeoAdmin):
    inlines = (QuestionAnswerInline,)
    search_fields = ("name", "code")


@admin.register(Academy)
class AcademyAdmin(OSMGeoAdmin):
    inlines = (QuestionAnswerInline,)
    search_fields = ("name",)
