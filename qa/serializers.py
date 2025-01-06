from rest_framework import serializers

from .models import QuestionAnswer, QuestionAnswerGlobal


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = ("id", "title_fr", "content_fr", "title_en", "content_en", "content_type", "object_id", "territory")

    territory = serializers.CharField(source="territory.name", read_only=True)


class QuestionAnswerGlobalSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswerGlobal
        fields = ("id", "title_fr", "content_fr", "title_en", "content_en")
