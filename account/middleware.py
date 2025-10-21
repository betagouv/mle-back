from django.shortcuts import redirect
from django.urls import reverse


class AdminLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated:
            return response

        if request.path != reverse("admin:index"):
            return response

        if request.user.owners.exists() and request.user.is_staff:
            return redirect("admin:accommodation_accommodation_changelist")

        return response
