from account.services import send_student_registration_email
from account.models import StudentRegistrationToken
from .factories import StudentFactory
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
