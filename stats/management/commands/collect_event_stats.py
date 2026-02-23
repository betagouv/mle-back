from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from stats.models import EventStats
from stats.services import MatomoAPIService


class Command(BaseCommand):
    help = 'Collect weekly event statistics from Matomo'

    def handle(self, *args, **options):
        service = MatomoAPIService()

        date_to = datetime.now().date() - timedelta(days=1)
        date_from = date_to - timedelta(days=6)

        events = service.get_all_events(
            date_from.strftime('%Y-%m-%d'),
            date_to.strftime('%Y-%m-%d')
        )

        for event in events:
            EventStats.objects.create(
                period='weekly',
                date_from=date_from,
                date_to=date_to,
                category=event['category'],
                action=event['action'],
                nb_events=event['nb_events'],
                nb_unique_events=event['nb_unique_events'],
                event_value=event['event_value'],
            )

        self.stdout.write(self.style.SUCCESS(
            f'{len(events)} event stats collected for {date_from} to {date_to}'
        ))
