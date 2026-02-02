from collections import defaultdict
from typing import Callable, Type

import logging

logger = logging.getLogger(__name__)


class AccommodationEventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable):
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            return
        logger.warning(f"Handler {handler} already subscribed to event {event_type}")

    def publish(self, event):
        for handler in self._handlers[type(event)]:
            handler(event)


accommodation_event_bus = AccommodationEventBus()
