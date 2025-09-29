from django.urls import path

from .views import magic_login_view, request_magic_link

urlpatterns = [
    path("magic-login/", magic_login_view, name="magic_login"),
    path("request-magic-link/", request_magic_link, name="request_magic_link"),
]
