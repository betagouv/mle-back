from unittest import mock

import pytest
from sib_api_v3_sdk.rest import ApiException

from notifications.exceptions import EmailDeliveryError
from notifications.gateways.brevo_email_gateway import BrevoEmailGateway
from tests.account.factories import UserFactory


@pytest.fixture
def brevo_settings(settings):
    settings.BREVO_API_KEY = "test-api-key"
    settings.BREVO_TEMPLATES_ID = {
        "magic-link": 101,
        "student-validation": 202,
        "student-password-reset": 303,
    }
    return settings


@pytest.mark.django_db
def test_send_magic_link_uses_expected_payload(brevo_settings):
    user = UserFactory(first_name="Ada", last_name="Lovelace", username="ada")
    gateway = BrevoEmailGateway()

    with (
        mock.patch("notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.SendSmtpEmail") as mock_email,
        mock.patch(
            "notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email"
        ) as mock_send,
    ):
        mock_email.return_value = mock.sentinel.email

        gateway.send_magic_link(to_user=user, magic_link="https://example.com/magic")

        mock_email.assert_called_once_with(
            to=[{"email": user.email, "name": "Ada Lovelace"}],
            template_id=brevo_settings.BREVO_TEMPLATES_ID["magic-link"],
            params={"MAGIC_LINK": "https://example.com/magic"},
            tags=["magic-link"],
        )
        mock_send.assert_called_once_with(mock.sentinel.email)


@pytest.mark.django_db
def test_send_account_validation_uses_expected_payload(brevo_settings):
    user = UserFactory(first_name="Linus", last_name="Torvalds", username="lt")
    gateway = BrevoEmailGateway()

    with (
        mock.patch("notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.SendSmtpEmail") as mock_email,
        mock.patch(
            "notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email"
        ) as mock_send,
    ):
        mock_email.return_value = mock.sentinel.email

        gateway.send_account_validation(
            to_user=user,
            validation_link="https://example.com/validate",
        )

        mock_email.assert_called_once_with(
            to=[{"email": user.email, "name": "Linus Torvalds"}],
            template_id=brevo_settings.BREVO_TEMPLATES_ID["student-validation"],
            params={
                "FIRST_NAME": "Linus",
                "LAST_NAME": "Torvalds",
                "VALIDATION_LINK": "https://example.com/validate",
            },
            tags=["student-validation"],
        )
        mock_send.assert_called_once_with(mock.sentinel.email)


@pytest.mark.django_db
def test_send_reset_password_uses_expected_payload(brevo_settings):
    user = UserFactory(first_name="Grace", last_name="Hopper", username="hopper")
    gateway = BrevoEmailGateway()

    with (
        mock.patch("notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.SendSmtpEmail") as mock_email,
        mock.patch(
            "notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email"
        ) as mock_send,
    ):
        mock_email.return_value = mock.sentinel.email

        gateway.send_reset_password(
            to_user=user,
            reset_link="https://example.com/reset",
        )

        mock_email.assert_called_once_with(
            to=[{"email": user.email, "name": "Grace Hopper"}],
            template_id=brevo_settings.BREVO_TEMPLATES_ID["student-password-reset"],
            params={"RESET_LINK": "https://example.com/reset"},
            tags=["student-password-reset"],
        )
        mock_send.assert_called_once_with(mock.sentinel.email)


@pytest.mark.django_db
def test_send_raises_email_delivery_error_on_api_failure(brevo_settings):
    user = UserFactory()
    gateway = BrevoEmailGateway()

    with mock.patch(
        "notifications.gateways.brevo_email_gateway.sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email",
        side_effect=ApiException(status=500, reason="Boom"),
    ):
        with pytest.raises(EmailDeliveryError):
            gateway.send_magic_link(to_user=user, magic_link="https://example.com/magic")
