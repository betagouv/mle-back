from django.urls import path

from .views import AccommodationDetailView, AccommodationListView, MyAccommodationListView

urlpatterns = [
    path("my/", MyAccommodationListView.as_view(), name="my-accommodation-list"),
    path("<slug:slug>/", AccommodationDetailView.as_view(), name="accommodation-detail"),
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
