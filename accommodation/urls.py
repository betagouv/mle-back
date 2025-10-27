from django.urls import path

from .views import (
    AccommodationDetailView,
    AccommodationListView,
    MyAccommodationDetailView,
    MyAccommodationImageUploadView,
    MyAccommodationListView,
)

urlpatterns = [
    path("my/", MyAccommodationListView.as_view(), name="my-accommodation-list"),
    path("my/<slug:slug>/", MyAccommodationDetailView.as_view(), name="my-accommodation-detail"),
    path("<slug:slug>/", AccommodationDetailView.as_view(), name="accommodation-detail"),
    path("my/<slug:slug>/upload/", MyAccommodationImageUploadView.as_view(), name="my-accommodation-upload"),
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
