from django.urls import path

from .views import AcademyListAPIView, CityListAPIView, DepartmentListAPIView, TerritoryCombinedListAPIView

urlpatterns = [
    path("academies/", AcademyListAPIView.as_view(), name="academies-list"),
    path("cities/", CityListAPIView.as_view(), name="cities-list"),
    path("departments/", DepartmentListAPIView.as_view(), name="departments-list"),
    path("", TerritoryCombinedListAPIView.as_view(), name="territory-combined-list"),
]
