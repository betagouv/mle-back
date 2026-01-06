from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import logging
from notifications.factories import get_email_gateway
from notifications.services import send_reset_password
from notifications.exceptions import EmailDeliveryError

from account.models import Student

logger = logging.getLogger(__name__)


def build_password_reset_link(user, frontend_base_url: str) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)

    return f"{frontend_base_url}/reinitialiser-son-mot-de-passe?uid={uid}&token={token}"


def request_password_reset(email: str) -> None:
    student = Student.objects.filter(user__email=email).first()
    if not student:
        return
    password_reset_link = build_password_reset_link(student.user, f"{settings.FRONT_SITE_URL}")
    email_gateway = get_email_gateway()
    try:
        send_reset_password(student.user, password_reset_link, email_gateway)
    except EmailDeliveryError:
        logger.error(f"Failed to send password reset link to user {student.user.email}")
