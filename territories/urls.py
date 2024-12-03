from django.urls import path

from .views import TerritoryCombinedListAPIView

urlpatterns = [
    path("", TerritoryCombinedListAPIView.as_view(), name="territory-combined-list"),
]
