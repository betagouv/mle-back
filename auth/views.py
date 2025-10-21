import sib_api_v3_sdk
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
from sib_api_v3_sdk.rest import ApiException

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

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.get_full_name() or user.username}],
            template_id=settings.BREVO_TEMPLATES_ID.get("magic-link"),
            params={"MAGIC_LINK": magic_link},
            tags=["magic-link"],
        )

        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException:
            pass
    return redirect("/admin/login/")


class RequestMagicLinkAPIView(APIView):
    authentication_classes = []
    permission_classes = []

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

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.get_full_name() or user.username}],
            template_id=settings.BREVO_TEMPLATES_ID.get("magic-link"),
            params={"MAGIC_LINK": magic_link},
            tags=["magic-link"],
        )

        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException:
            pass

        return Response({"detail": generic_message}, status=status.HTTP_200_OK)


class CheckMagicLinkAPIView(APIView):
    authentication_classes = []
    permission_classes = []

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
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
