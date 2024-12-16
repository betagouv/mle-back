from django.urls import path

from .views import AccommodationDetailView, AccommodationListView

urlpatterns = [
    path("<slug:slug>/", AccommodationDetailView.as_view(), name="accommodation-detail"),
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
