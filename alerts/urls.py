from django.urls import path
from .views import AccommodationAlertViewSet


urlpatterns = [
    path("", AccommodationAlertViewSet.as_view({"get": "list", "post": "create"}), name="accommodation-alert-list"),
    path(
        "<int:pk>/",
        AccommodationAlertViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="accommodation-alert-detail",
    ),
]
