import sib_api_v3_sdk
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy
from sesame.utils import get_token
from sib_api_v3_sdk.rest import ApiException

User = get_user_model()


def magic_login_view(request):
    token = request.GET.get("sesame")
    if not token:
        return HttpResponseBadRequest("Missing token")

    user = authenticate(request, sesame=token)
    if user and user.is_staff and user.is_active:
        login(request, user)
        return redirect("/admin/")

    return HttpResponseBadRequest("Invalid token or not authorized")


def request_magic_link(request):
    if request.method == "POST":
        email = request.POST.get("email")
        message = gettext_lazy(
            "If an account exists with the email %(email)s, you will receive a link to log in. "
            "Please contact %(bizdev)s in case of problem." % {"email": email, "bizdev": settings.BIZDEV_EMAIL}
        )
        messages.success(request, message)
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
