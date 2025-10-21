from django.urls import path

from .views import CheckMagicLinkAPIView, RequestMagicLinkAPIView, magic_login_view, request_magic_link

urlpatterns = [
    path("magic-login/", magic_login_view, name="magic_login_v0"),
    path("request-magic-link/", request_magic_link, name="request_magic_link_v0"),
    path("magic-link/", RequestMagicLinkAPIView.as_view(), name="request-magic-link"),
    path("check/", CheckMagicLinkAPIView.as_view(), name="check-magic-link"),
]
