from rest_framework import serializers

from .models import QuestionAnswer


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = ("id", "title_fr", "content_fr", "content_type", "object_id", "territory")

    territory = serializers.CharField(source="territory.name", read_only=True)
