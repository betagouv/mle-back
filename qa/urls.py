from django.urls import path

from .views import QuestionAnswerListByTerritoryAPIView

urlpatterns = [
    path("", QuestionAnswerListByTerritoryAPIView.as_view(), name="questionanswers-by-territory"),
]
