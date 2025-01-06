from django.urls import path

from .views import AcademyListAPIView, CitiesListApiView, TerritoryCombinedListAPIView

urlpatterns = [
    path("academies/", AcademyListAPIView.as_view(), name="academies-list"),
    path("cities/", CitiesListApiView.as_view(), name="cities-list"),
    path("", TerritoryCombinedListAPIView.as_view(), name="territory-combined-list"),
]
