from django.urls import path

from .views import QuestionAnswerReadOnlyViewSet

urlpatterns = [
    path("", QuestionAnswerReadOnlyViewSet.as_view({"get": "list"}), name="questionanswers-list-create"),
]
