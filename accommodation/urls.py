from django.urls import path

from .views import AccommodationListView

urlpatterns = [
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
