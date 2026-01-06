from notifications.gateways.brevo_email_gateway import BrevoEmailGateway
from notifications.types import EmailGateway


def get_email_gateway() -> EmailGateway:
    return BrevoEmailGateway()
