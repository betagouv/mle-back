from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    OwnerViewSet,
    StudentDossierFacileCompleteConnectView,
    StudentDossierFacileStartConnectView,
    StudentDossierFacileStatusView,
    StudentDossierFacileWebhookView,
    StudentGetTokenView,
    StudentLogoutView,
    StudentPasswordResetConfirmView,
    StudentRegistrationView,
    StudentRegistrationValidationView,
    StudentRequestPasswordResetView,
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
    path(
        "students/dossierfacile/connect/start/",
        StudentDossierFacileStartConnectView.as_view(),
        name="student-dossierfacile-connect-start",
    ),
    path(
        "students/dossierfacile/connect/complete/",
        StudentDossierFacileCompleteConnectView.as_view(),
        name="student-dossierfacile-connect-complete",
    ),
    path(
        "students/dossierfacile/status/",
        StudentDossierFacileStatusView.as_view(),
        name="student-dossierfacile-status",
    ),
    path(
        "students/dossierfacile/webhook/",
        StudentDossierFacileWebhookView.as_view(),
        name="student-dossierfacile-webhook",
    ),
]
