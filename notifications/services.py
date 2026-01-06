from notifications.types import EmailGateway
from django.contrib.auth import get_user_model

User = get_user_model()


def send_magic_link(user: User, magic_link: str, email_gateway: EmailGateway) -> None:
    email_gateway.send_magic_link(
        to_user=user,
        magic_link=magic_link,
    )


def send_account_validation(user: User, validation_link: str, email_gateway: EmailGateway) -> None:
    email_gateway.send_account_validation(
        to_user=user,
        validation_link=validation_link,
    )


def send_reset_password(user: User, reset_link: str, email_gateway: EmailGateway) -> None:
    email_gateway.send_reset_password(
        to_user=user,
        reset_link=reset_link,
    )
