from django.urls import path

from .views import (
    AcademyListAPIView,
    CityDetailView,
    CityListAPIView,
    DepartmentListAPIView,
    NewsletterSubscriptionAPIView,
    TerritoryCombinedListAPIView,
)

urlpatterns = [
    path("academies/", AcademyListAPIView.as_view(), name="academies-list"),
    path("cities/<slug:slug>/details", CityDetailView.as_view(), name="city-detail"),
    path("cities/", CityListAPIView.as_view(), name="cities-list"),
    path("departments/", DepartmentListAPIView.as_view(), name="departments-list"),
    path("newsletter/subscribe/", NewsletterSubscriptionAPIView.as_view(), name="newsletter-subscription"),
    path("", TerritoryCombinedListAPIView.as_view(), name="territory-combined-list"),
]
