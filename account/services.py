import sib_api_v3_sdk
from django.conf import settings

from sib_api_v3_sdk.rest import ApiException


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
