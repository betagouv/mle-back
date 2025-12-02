from django.urls import path

from .views import (
    AccommodationDetailView,
    AccommodationListView,
    FavoriteAccommodationViewSet,
    MyAccommodationDetailView,
    MyAccommodationImageUploadView,
    MyAccommodationListView,
)

urlpatterns = [
    path("my/", MyAccommodationListView.as_view(), name="my-accommodation-list"),
    path("my/<slug:slug>/", MyAccommodationDetailView.as_view(), name="my-accommodation-detail"),
    path("my/<slug:slug>/upload/", MyAccommodationImageUploadView.as_view(), name="my-accommodation-upload"),
    path(
        "favorites/",
        FavoriteAccommodationViewSet.as_view({"get": "list", "post": "create"}),
        name="favorite-accommodation-list",
    ),
    path(
        "favorites/<slug:slug>/",
        FavoriteAccommodationViewSet.as_view({"delete": "destroy"}),
        name="favorite-accommodation-detail",
    ),
    path("<slug:slug>/", AccommodationDetailView.as_view(), name="accommodation-detail"),
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
