from django.urls import path

from .views import OwnerViewSet

urlpatterns = [
    path("owners/", OwnerViewSet.as_view({"get": "list"}), name="owner-list"),
]
