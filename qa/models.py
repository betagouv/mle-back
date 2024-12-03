from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class QuestionAnswer(models.Model):
    title_fr = models.CharField(max_length=200)
    title_en = models.CharField(max_length=200, null=True, blank=True)
    content_fr = models.TextField()
    content_en = models.TextField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    territory = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.title_fr
