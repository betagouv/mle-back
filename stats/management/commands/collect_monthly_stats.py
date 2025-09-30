from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from stats.models import Stats
from stats.services import MatomoAPIService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Collect monthly statistics from Matomo API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            help='Specific month to collect stats for (YYYY-MM). If not provided, uses last month.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force collection even if data already exists for this period'
        )

    def handle(self, *args, **options):
        try:
            # Determine the date range
            if options['month']:
                year, month = map(int, options['month'].split('-'))
            else:
                # Get last month
                today = timezone.now().date()
                if today.month == 1:
                    year = today.year - 1
                    month = 12
                else:
                    year = today.year
                    month = today.month - 1
            
            # Get first and last day of the month
            start_date = datetime(year, month, 1).date()
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            
            self.stdout.write(f"Collecting monthly stats for {start_date} to {end_date}")
            
            # Check if data already exists
            existing_stats = Stats.objects.filter(
                period='monthly',
                date_from=start_date,
                date_to=end_date
            ).first()
            
            if existing_stats and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        f"Stats already exist for month {start_date.strftime('%Y-%m')}. Use --force to override."
                    )
                )
                return
            
            # Collect data from Matomo
            matomo_service = MatomoAPIService()
            
            # Get current month data
            stats_data = matomo_service.get_complete_stats(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Get previous month for evolution calculation
            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1
            
            prev_start = datetime(prev_year, prev_month, 1).date()
            prev_last_day = monthrange(prev_year, prev_month)[1]
            prev_end = datetime(prev_year, prev_month, prev_last_day).date()
            
            evolution_data = matomo_service.get_evolution_data(
                f"{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}",
                f"{prev_start.strftime('%Y-%m-%d')},{prev_end.strftime('%Y-%m-%d')}"
            )
            
            # Create or update stats record
            stats_obj, created = Stats.objects.update_or_create(
                period='monthly',
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
                    f"{action} monthly stats for {start_date.strftime('%Y-%m')} "
                    f"(ID: {stats_obj.id})"
                )
            )
            
            # Log key metrics
            self.stdout.write(f"  - Unique visitors: {stats_data['unique_visitors']}")
            self.stdout.write(f"  - Page views: {stats_data['page_views']}")
            self.stdout.write(f"  - Bounce rate: {stats_data['bounce_rate_percentage']}%")
            
        except Exception as e:
            logger.error(f"Error collecting monthly stats: {e}")
            self.stdout.write(
                self.style.ERROR(f"Failed to collect monthly stats: {e}")
            )
            raise