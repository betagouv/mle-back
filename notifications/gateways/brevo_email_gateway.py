from django.conf import settings
from django.contrib.auth import get_user_model
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from notifications.exceptions import EmailDeliveryError

User = get_user_model()


class BrevoEmailGateway:
    """
    Infrastructure-level email sender.
    This is the ONLY place that knows about Brevo.
    """

    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_client = sib_api_v3_sdk.ApiClient(configuration)
        self.api = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

    def _send(
        self,
        *,
        to_email: str,
        to_name: str,
        template_id: int,
        params: dict,
        tags: list[str],
    ) -> None:
        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name}],
            template_id=template_id,
            params=params,
            tags=tags,
        )

        try:
            self.api.send_transac_email(email)
        except ApiException as exc:
            raise EmailDeliveryError("Failed to send email via Brevo") from exc

    # ---- Public intent-based methods ----

    def send_magic_link(
        self,
        *,
        to_user: User,
        magic_link: str,
    ) -> None:
        self._send(
            to_email=to_user.email,
            to_name=to_user.get_full_name() or to_user.username,
            template_id=settings.BREVO_TEMPLATES_ID["magic-link"],
            params={"MAGIC_LINK": magic_link},
            tags=["magic-link"],
        )

    def send_account_validation(
        self,
        *,
        to_user: User,
        validation_link: str,
    ) -> None:
        self._send(
            to_email=to_user.email,
            to_name=to_user.get_full_name() or to_user.username,
            template_id=settings.BREVO_TEMPLATES_ID["student-validation"],
            params={
                "FIRST_NAME": to_user.first_name,
                "LAST_NAME": to_user.last_name,
                "VALIDATION_LINK": validation_link,
            },
            tags=["student-validation"],
        )

    def send_reset_password(
        self,
        *,
        to_user: User,
        reset_link: str,
    ) -> None:
        self._send(
            to_email=to_user.email,
            to_name=to_user.get_full_name() or to_user.username,
            template_id=settings.BREVO_TEMPLATES_ID["student-password-reset"],
            params={"RESET_LINK": reset_link},
            tags=["student-password-reset"],
        )
