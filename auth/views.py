from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from sesame.utils import get_token, get_user

from account.serializers import UserSerializer
from notifications.factories import get_email_gateway
from notifications.services import send_magic_link

User = get_user_model()


def magic_login_view(request):
    # NOTE: this is used by BO v0, will be deprecated in BO v1
    token = request.GET.get("sesame")
    if not token:
        return HttpResponseBadRequest("Missing token")

    user = authenticate(request, sesame=token)
    if user and user.is_staff and user.is_active:
        login(request, user)
        return redirect("/admin/")

    return HttpResponseBadRequest("Invalid token or not authorized")


def request_magic_link(request):
    # NOTE: this is used by BO v0, will be deprecated in BO v1
    if request.method == "POST":
        email = request.POST.get("email")
        generic_message = gettext_lazy(
            "If an account exists with the email %(email)s, you will receive a link to log in. "
            "Please contact %(bizdev)s in case of problem."
        ) % {"email": email, "bizdev": settings.BIZDEV_EMAIL}

        messages.success(request, generic_message)
        try:
            user = User.objects.get(email=email, is_staff=True, is_active=True)
            token = get_token(user)
            magic_link = f"{request.build_absolute_uri('/admin-auth/magic-login/')}?sesame={token}"

        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return redirect("/admin/login/")

        email_gateway = get_email_gateway()
        send_magic_link(user, magic_link, email_gateway)
    return redirect("/admin/login/")


class RequestMagicLinkAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = None

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        generic_message = _(
            "If an account exists with this email, you will receive a link to log in. "
            "Please contact %(bizdev)s in case of problem."
        ) % {"bizdev": settings.BIZDEV_EMAIL}

        try:
            user = User.objects.get(email=email, is_staff=True, is_active=True)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return Response({"detail": generic_message}, status=status.HTTP_200_OK)

        token = get_token(user)
        magic_link = f"{settings.FRONT_SITE_URL}/verification?sesame={token}"

        email_gateway = get_email_gateway()
        send_magic_link(user, magic_link, email_gateway)

        return Response({"detail": generic_message}, status=status.HTTP_200_OK)


class CheckMagicLinkAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = None

    def post(self, request):
        token = request.data.get("sesame")

        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user(token)

        if not user or not user.is_active:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {
                "access": access_token,
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
