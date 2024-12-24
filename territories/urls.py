from django.urls import path

from .views import AcademyListAPIView, TerritoryCombinedListAPIView

urlpatterns = [
    path("academies/", AcademyListAPIView.as_view(), name="academies-list"),
    path("", TerritoryCombinedListAPIView.as_view(), name="territory-combined-list"),
]
