from rest_framework import viewsets

from .models import QuestionAnswer
from .serializers import QuestionAnswerSerializer


class QuestionAnswerReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionAnswer.objects.all()
    serializer_class = QuestionAnswerSerializer
