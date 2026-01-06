from account.services import (
    build_password_reset_link,
    request_password_reset,
)
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .factories import StudentFactory, UserFactory
from unittest import mock
import pytest


@pytest.mark.django_db
def test_build_password_reset_link():
    user = UserFactory.create()
    link = build_password_reset_link(user, "https://www.example.com")
    uid = link.split("uid=")[1].split("&")[0]
    token = link.split("token=")[1]
    assert uid == urlsafe_base64_encode(force_bytes(user.pk))
    assert PasswordResetTokenGenerator().check_token(user, token)


@pytest.mark.django_db
def test_request_password_reset():
    student = StudentFactory.create()
    expected_link = build_password_reset_link(student.user, "http://127.0.0.1:8000")
    email_gateway = mock.Mock()

    with (
        mock.patch("account.services.get_email_gateway", return_value=email_gateway) as mock_get_gateway,
        mock.patch("account.services.send_reset_password") as mock_send,
    ):
        request_password_reset(student.user.email)

    mock_get_gateway.assert_called_once_with()
    mock_send.assert_called_once_with(student.user, expected_link, email_gateway)
