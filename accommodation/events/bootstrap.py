# accommodation/events/bootstrap.py
from functools import partial
from .notifiers import DatabaseNotifier, get_notifier
from .bus import accommodation_event_bus
from .events import (
    AccommodationCreatedEvent,
    AccommodationUpdatedEvent,
)
from .handlers import (
    handle_accommodation_created,
    handle_accommodation_updated,
)

_bootstrapped = False


def bootstrap_accommodation_events():
    global _bootstrapped
    if _bootstrapped:
        return

    notifier = get_notifier()
    db_notifier = DatabaseNotifier()

    accommodation_event_bus.subscribe(
        AccommodationCreatedEvent,
        partial(handle_accommodation_created, notifier=notifier),
    )
    accommodation_event_bus.subscribe(
        AccommodationCreatedEvent,
        partial(handle_accommodation_created, notifier=db_notifier),
    )
    accommodation_event_bus.subscribe(
        AccommodationUpdatedEvent,
        partial(handle_accommodation_updated, notifier=notifier),
    )
    accommodation_event_bus.subscribe(
        AccommodationUpdatedEvent,
        partial(handle_accommodation_updated, notifier=db_notifier),
    )

    _bootstrapped = True
