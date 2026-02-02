from .events import AccommodationCreatedEvent, AccommodationUpdatedEvent
from .notifiers import Notifier


def handle_accommodation_created(event: AccommodationCreatedEvent, notifier: Notifier):
    notifier.notify(event)


def handle_accommodation_updated(event: AccommodationUpdatedEvent, notifier: Notifier):
    notifier.notify(event)
