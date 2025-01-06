from django.urls import path

from .views import QuestionAnswerGlobalListAPIView, QuestionAnswerListByTerritoryAPIView

urlpatterns = [
    path("by-territory", QuestionAnswerListByTerritoryAPIView.as_view(), name="questionanswers-by-territory"),
    path("global", QuestionAnswerGlobalListAPIView.as_view(), name="questionanswers-global"),
]
