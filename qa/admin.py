from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_summernote.widgets import SummernoteWidget

from .models import QuestionAnswer


class QuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = QuestionAnswer
        fields = ["title_fr", "title_en", "content_fr", "content_en", "content_type", "object_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content_type"].queryset = ContentType.objects.filter(model__in=["city", "department", "academy"])

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.content_type and instance.object_id:
            instance.territory = instance.content_type.get_object_for_this_type(id=instance.object_id)
        if commit:
            instance.save()
        return instance


class QuestionAnswerAdmin(admin.ModelAdmin):
    form = QuestionAnswerForm
    list_display = ("title_fr", "territory_name")
    search_fields = ("title_fr", "content_fr")

    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }

    def territory_name(self, obj):
        return obj.territory.name if obj.territory else ""

    territory_name.short_description = "Territoire"


admin.site.register(QuestionAnswer, QuestionAnswerAdmin)
