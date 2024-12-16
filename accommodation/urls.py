from django.urls import path

from .views import AccommodationListView, AccommodationDetailView

urlpatterns = [
    path("<int:pk>/", AccommodationDetailView.as_view(), name="accommodation-detail"),
    path("", AccommodationListView.as_view(), name="accommodation-list"),
]
