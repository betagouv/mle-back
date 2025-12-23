from django.urls import path

from .views import OwnerViewSet, StudentRegistrationView, StudentRegistrationValidationView

urlpatterns = [
    path("owners/", OwnerViewSet.as_view({"get": "list"}), name="owner-list"),
    path("students/register/", StudentRegistrationView.as_view(), name="student-register"),
    path("students/validate/", StudentRegistrationValidationView.as_view(), name="student-validate"),
]
