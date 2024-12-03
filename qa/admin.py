from django.contrib.contenttypes.admin import GenericStackedInline
from django.db import models
from django_summernote.widgets import SummernoteWidget

from .models import QuestionAnswer


class QuestionAnswerInline(GenericStackedInline):
    model = QuestionAnswer
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": SummernoteWidget},
    }
