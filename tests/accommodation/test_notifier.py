import pytest

from accommodation.events.events import AccommodationCreatedEvent
from accommodation.events.handlers import handle_accommodation_created
from accommodation.events.notifiers import MattermostNotifier
from tests.account.factories import OwnerFactory, UserFactory
from tests.accommodation.factories import AccommodationFactory


@pytest.mark.django_db
def test_mattermost_notifier_sends_message_via_handler(mock_requests):
    user = UserFactory(first_name="Jane", last_name="Doe")
    owner = OwnerFactory(users=[user])
    accommodation = AccommodationFactory(owner=owner, name="Résidence Alpha", city="Paris")

    webhook_url = "https://mattermost.example/hooks/abc123"
    mock_requests.post(webhook_url, status_code=200)

    notifier = MattermostNotifier(webhook_url=webhook_url)
    event = AccommodationCreatedEvent(accommodation_id=accommodation.id, user_id=user.id)

    handle_accommodation_created(event, notifier)

    assert mock_requests.called
    assert mock_requests.request_history[-1].url == webhook_url
    assert mock_requests.request_history[-1].json()["text"] == event.to_message()
