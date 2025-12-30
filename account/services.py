import sib_api_v3_sdk
from django.conf import settings

from sib_api_v3_sdk.rest import ApiException

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


def send_student_registration_email(student, validation_link):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": student.user.email, "name": student.user.get_full_name() or student.user.username}],
        template_id=settings.BREVO_TEMPLATES_ID.get("student-validation"),
        params={
            "FIRST_NAME": student.user.first_name,
            "LAST_NAME": student.user.last_name,
            "VALIDATION_LINK": validation_link,
        },
        tags=["student-validation"],
    )
    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException:
        pass


def send_student_password_reset_email(student, reset_link):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": student.user.email, "name": student.user.get_full_name() or student.user.username}],
        template_id=settings.BREVO_TEMPLATES_ID.get("student-password-reset"),
        params={
            "RESET_LINK": reset_link,
        },
        tags=["student-password-reset"],
    )
    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException:
        pass


def build_password_reset_link(user, frontend_base_url: str) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)

    return f"{frontend_base_url}/mot-de-passe-oublie?uid={uid}&token={token}"
