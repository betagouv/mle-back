from django.contrib import admin

from qa.admin import QuestionAnswerInline

from .models import Academy, City, Department


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name", "postal_codes"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name", "code"]


@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    inlines = [QuestionAnswerInline]
    search_fields = ["name"]
