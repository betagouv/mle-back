from account.services import (
    send_student_password_reset_email,
    send_student_registration_email,
    build_password_reset_link,
)
from account.models import StudentRegistrationToken
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .factories import StudentFactory, UserFactory
from unittest import mock
import pytest


@pytest.mark.django_db
def test_send_student_registration_email():
    student = StudentFactory.create()
    token = StudentRegistrationToken.get_or_create_for_user(student.user)
    url = f"https://www.example.com?validation_token={token.token}"
    with mock.patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email") as mock_send_email:
        mock_send_email.return_value = None
        send_student_registration_email(student, url)
        assert mock_send_email.call_count == 1


@pytest.mark.django_db
def test_build_password_reset_link():
    user = UserFactory.create()
    link = build_password_reset_link(user, "https://www.example.com")
    uid = link.split("uid=")[1].split("&")[0]
    token = link.split("token=")[1]
    assert uid == urlsafe_base64_encode(force_bytes(user.pk))
    assert PasswordResetTokenGenerator().check_token(user, token)


@pytest.mark.django_db
def test_send_student_password_reset_email():
    student = StudentFactory.create()
    link = build_password_reset_link(student.user, "https://www.example.com")
    with mock.patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email") as mock_send_email:
        mock_send_email.return_value = None
        send_student_password_reset_email(student, link)
        assert mock_send_email.call_count == 1
