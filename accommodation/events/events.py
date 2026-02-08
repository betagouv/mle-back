from dataclasses import dataclass
import json
from typing import Protocol, ClassVar

from accommodation.models import Accommodation
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings


class AccommodationEvent(Protocol):
    accommodation_id: int
    user_id: int

    def to_message(self) -> str: ...


@dataclass
class BaseAccommodationEvent:
    accommodation_id: int
    user_id: int

    action_label: ClassVar[str]

    def to_message(self) -> str:
        accommodation = Accommodation.objects.get(id=self.accommodation_id)
        user = User.objects.get(id=self.user_id)

        accommodation_url = accommodation.get_absolute_url()
        user_path = reverse(
            "admin:auth_user_change",
            args=[user.id],
        )

        user_url = f"{settings.ADMIN_SITE_URL}{user_path}"

        return (
            f"Résidence {self.action_label}: "
            f"[{accommodation.name}]({accommodation_url}) "
            f"par [{user.get_full_name()}]({user_url})"
        )


@dataclass
class AccommodationCreatedEvent(BaseAccommodationEvent):
    action_label: ClassVar[str] = "créée"


@dataclass
class AccommodationUpdatedEvent(BaseAccommodationEvent):
    data_diff: dict
    action_label: ClassVar[str] = "mise à jour"

    def to_message(self) -> str:
        return (
            super().to_message()
            + "\n\n"
            + "**Diff :**\n\n"
            + "```json\n"
            + json.dumps(self.data_diff, indent=4, ensure_ascii=False)
            + "\n```\n"
        )
