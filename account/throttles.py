from rest_framework.throttling import SimpleRateThrottle


class PasswordResetThrottle(SimpleRateThrottle):
    """
    Throttle password reset requests to prevent abuse.
    Throttles by email address and IP address.
    """

    scope = "password_reset"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "").lower()
        ident = f"{self.get_ident(request)}:{email}"

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }
