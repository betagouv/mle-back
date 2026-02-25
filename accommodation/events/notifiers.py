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


class DatabaseNotifier:
    def notify(self, event: AccommodationEvent) -> None:
        from stats.models import AccommodationChangeLog
        from accommodation.models import Accommodation

        accommodation = Accommodation.objects.select_related("owner").get(
            id=event.accommodation_id
        )

        from .events import AccommodationCreatedEvent

        action = "created" if isinstance(event, AccommodationCreatedEvent) else "updated"
        data_diff = getattr(event, "data_diff", {})

        AccommodationChangeLog.objects.create(
            accommodation=accommodation,
            user_id=event.user_id,
            owner=accommodation.owner,
            action=action,
            data_diff=data_diff,
        )


def get_notifier() -> Notifier:
    if settings.ENVIRONMENT == "production":
        if not settings.MATTERMOST_WEBHOOK_URL:
            raise RuntimeError("MATTERMOST_WEBHOOK_URL must be set in environment variables for production")
        return MattermostNotifier(
            webhook_url=settings.MATTERMOST_WEBHOOK_URL,
        )

    return NullNotifier()
