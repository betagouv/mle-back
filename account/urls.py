from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    OwnerViewSet,
    StudentRegistrationView,
    StudentRegistrationValidationView,
    StudentGetTokenView,
    StudentRequestPasswordResetView,
    StudentPasswordResetConfirmView,
    StudentLogoutView,
)

urlpatterns = [
    path("owners/", OwnerViewSet.as_view({"get": "list"}), name="owner-list"),
    path("students/register/", StudentRegistrationView.as_view(), name="student-register"),
    path("students/validate/", StudentRegistrationValidationView.as_view(), name="student-validate"),
    path("students/token/", StudentGetTokenView.as_view(), name="student-token"),
    path("students/refresh/", TokenRefreshView.as_view(), name="student-refresh-token"),
    path(
        "students/request-password-reset/",
        StudentRequestPasswordResetView.as_view(),
        name="student-request-password-reset",
    ),
    path(
        "students/password-reset-confirm/<uidb64>/<token>/",
        StudentPasswordResetConfirmView.as_view(),
        name="student-password-reset-confirm",
    ),
    path("students/logout/", StudentLogoutView.as_view(), name="student-logout"),
]
