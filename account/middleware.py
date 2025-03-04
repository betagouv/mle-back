from django.shortcuts import redirect
from django.urls import reverse


class AdminLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.user.is_authenticated
            and request.path == reverse("admin:index")
            and hasattr(request.user, "owner")
            and request.user.is_staff
        ):
            return redirect("admin:accommodation_accommodation_changelist")
        return response
