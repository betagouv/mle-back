from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.db import models
from django_summernote.widgets import SummernoteWidget

from .models import QuestionAnswer, QuestionAnswerGlobal


class QuestionAnswerInline(GenericStackedInline):
    model = QuestionAnswer
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }


@admin.register(QuestionAnswerGlobal)
class QuestionAnswerGlobalAdmin(admin.ModelAdmin):
    list_display = ("title_fr", "title_en", "content_fr", "content_en")
    search_fields = ("title_fr", "title_en", "content_fr", "content_en")
    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }
