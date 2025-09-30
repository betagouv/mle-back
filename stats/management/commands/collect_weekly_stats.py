from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from stats.models import Stats
from stats.services import MatomoAPIService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Collect weekly statistics from Matomo API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to collect stats for (YYYY-MM-DD). If not provided, uses last week.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force collection even if data already exists for this period'
        )

    def handle(self, *args, **options):
        try:
            # Determine the date range
            if options['date']:
                end_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            else:
                # Get last Monday to Sunday
                today = timezone.now().date()
                days_since_monday = today.weekday()
                last_monday = today - timedelta(days=days_since_monday + 7)
                end_date = last_monday + timedelta(days=6)  # Sunday
            
            start_date = end_date - timedelta(days=6)  # Monday
            
            self.stdout.write(f"Collecting weekly stats for {start_date} to {end_date}")
            
            # Check if data already exists
            existing_stats = Stats.objects.filter(
                period='weekly',
                date_from=start_date,
                date_to=end_date
            ).first()
            
            if existing_stats and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        f"Stats already exist for week {start_date} to {end_date}. Use --force to override."
                    )
                )
                return
            
            # Collect data from Matomo
            matomo_service = MatomoAPIService()
            
            # Get current week data
            stats_data = matomo_service.get_complete_stats(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Get previous week for evolution calculation
            prev_start = start_date - timedelta(days=7)
            prev_end = end_date - timedelta(days=7)
            
            evolution_data = matomo_service.get_evolution_data(
                f"{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}",
                f"{prev_start.strftime('%Y-%m-%d')},{prev_end.strftime('%Y-%m-%d')}"
            )
            
            # Create or update stats record
            stats_obj, created = Stats.objects.update_or_create(
                period='weekly',
                date_from=start_date,
                date_to=end_date,
                defaults={
                    'unique_visitors': stats_data['unique_visitors'],
                    'new_visits_percentage': stats_data['new_visits_percentage'],
                    'average_duration': stats_data['average_duration'],
                    'visitors_evolution_percentage': evolution_data['visitors_evolution'],
                    'bounce_rate_percentage': stats_data['bounce_rate_percentage'],
                    'bounce_rate_evolution_percentage': evolution_data['bounce_rate_evolution'],
                    'page_views': stats_data['page_views'],
                    'visitors_per_page': stats_data['visitors_per_page'],
                    'page_views_evolution_percentage': evolution_data['page_views_evolution'],
                    'top_pages': stats_data['top_pages'],
                    'main_entry_pages': stats_data['main_entry_pages'],
                    'main_sources': stats_data['main_sources'],
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} weekly stats for {start_date} to {end_date} "
                    f"(ID: {stats_obj.id})"
                )
            )
            
            # Log key metrics
            self.stdout.write(f"  - Unique visitors: {stats_data['unique_visitors']}")
            self.stdout.write(f"  - Page views: {stats_data['page_views']}")
            self.stdout.write(f"  - Bounce rate: {stats_data['bounce_rate_percentage']}%")
            
        except Exception as e:
            logger.error(f"Error collecting weekly stats: {e}")
            self.stdout.write(
                self.style.ERROR(f"Failed to collect weekly stats: {e}")
            )
            raise