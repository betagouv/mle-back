from typing import Protocol
import requests
from django.conf import settings
from .events import AccommodationEvent
import logging

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def notify(self, event: AccommodationEvent) -> None: ...


class NullNotifier:
    def notify(self, event: AccommodationEvent) -> None:
        logger.info(event.to_message())


class MattermostNotifier:
    def __init__(
        self,
        webhook_url: str,
        *,
        timeout: int = 5,
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def notify(self, event: AccommodationEvent) -> None:
        if not self.webhook_url:
            logger.warning("Mattermost notifier missing webhook_url.")
            return

        payload = {"text": event.to_message()}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            if response.status_code >= 400:
                logger.warning(
                    "Mattermost notification failed with status %s: %s",
                    response.status_code,
                    response.text,
                )
        except requests.RequestException:
            logger.exception("Mattermost notification failed.")


def get_notifier() -> Notifier:
    if settings.ENVIRONMENT == "production" or settings.ENVIRONMENT == "staging":
        if not settings.MATTERMOST_WEBHOOK_URL:
            raise RuntimeError("MATTERMOST_WEBHOOK_URL must be set in environment variables for production")
        return MattermostNotifier(
            webhook_url=settings.MATTERMOST_WEBHOOK_URL,
        )

    return NullNotifier()
