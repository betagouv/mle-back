from dataclasses import dataclass
from typing import Protocol

from accommodation.models import Accommodation
from django.contrib.auth.models import User
from django.urls import reverse


class AccommodationEvent(Protocol):
    accommodation_id: int
    user_id: int

    def to_message(self) -> str: ...


@dataclass
class BaseAccommodationEvent:
    accommodation_id: int
    user_id: int

    action_label: str  # e.g. "créée", "mise à jour"

    def to_message(self) -> str:
        accommodation = Accommodation.objects.get(id=self.accommodation_id)
        user = User.objects.get(id=self.user_id)

        accommodation_url = accommodation.get_absolute_url()
        user_url = reverse(
            "admin:auth_user_change",
            args=[user.id],
        )

        return (
            f"Résidence {self.action_label}: "
            f"[{accommodation.name}]({accommodation_url}) "
            f"par [{user.get_full_name()}]({user_url})"
        )


@dataclass
class AccommodationCreatedEvent(BaseAccommodationEvent):
    action_label: str = "créée"


@dataclass
class AccommodationUpdatedEvent(BaseAccommodationEvent):
    action_label: str = "mise à jour"
