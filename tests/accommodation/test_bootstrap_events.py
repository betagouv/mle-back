# accommodation/events/tests/test_bootstrap.py
import functools
import pytest
from unittest.mock import Mock, patch
from accommodation.events.bootstrap import bootstrap_accommodation_events
from accommodation.events.bus import accommodation_event_bus
from accommodation.events.events import (
    AccommodationCreatedEvent,
    AccommodationUpdatedEvent,
)
from accommodation.events.handlers import (
    handle_accommodation_created,
    handle_accommodation_updated,
)

import accommodation.events.bootstrap as bootstrap_module

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def reset_event_system():
    # reset bus handlers
    accommodation_event_bus._handlers.clear()

    # reset bootstrap guard
    bootstrap_module._bootstrapped = False

    yield

    # cleanup again (safety)
    accommodation_event_bus._handlers.clear()
    bootstrap_module._bootstrapped = False


def test_bootstrap_is_idempotent():
    # Act
    bootstrap_accommodation_events()
    bootstrap_accommodation_events()

    handlers = accommodation_event_bus._handlers

    assert len(handlers[AccommodationCreatedEvent]) == 1
    handler = handlers[AccommodationCreatedEvent][0]

    assert isinstance(handler, functools.partial)
    assert handler.func is handle_accommodation_created

    assert len(handlers[AccommodationUpdatedEvent]) == 1
    handler = handlers[AccommodationUpdatedEvent][0]

    assert isinstance(handler, functools.partial)
    assert handler.func is handle_accommodation_updated


def test_event_bus_does_not_register_same_handler_twice():
    from accommodation.events.bus import AccommodationEventBus

    bus = AccommodationEventBus()

    bus.subscribe(AccommodationCreatedEvent, handle_accommodation_created)
    bus.subscribe(AccommodationCreatedEvent, handle_accommodation_created)

    assert bus._handlers[AccommodationCreatedEvent] == [handle_accommodation_created]


def test_handler_called_once_after_multiple_bootstrap():
    mock_handler = Mock()

    # Patch WHERE THE HANDLER IS USED
    with patch.object(
        bootstrap_module,
        "handle_accommodation_created",
        mock_handler,
    ):
        # IMPORTANT: reset bootstrap guard
        bootstrap_module._bootstrapped = False
        accommodation_event_bus._handlers.clear()

        bootstrap_accommodation_events()
        bootstrap_accommodation_events()

        accommodation_event_bus.publish(AccommodationCreatedEvent(accommodation_id=1, user_id=1))

    mock_handler.assert_called_once()
