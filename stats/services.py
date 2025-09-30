import requests
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MatomoAPIService:
    """Service to interact with Matomo API and fetch website statistics"""
    
    def __init__(self):
        self.base_url = settings.MATOMO_URL
        self.token = settings.MATOMO_TOKEN
        self.site_id = settings.MATOMO_ID_SITE
        
    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Matomo API"""
        url = f"{self.base_url}/index.php"
        
        default_params = {
            'module': 'API',
            'method': method,
            'idSite': self.site_id,
            'token_auth': self.token,
            'format': 'json'
        }
        
        params.update(default_params)
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Matomo API request failed: {e}")
            raise
    
    def get_visitors_overview(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get visitors overview data"""
        return self._make_request(
            'VisitsSummary.get',
            {
                'date': f"{date_from},{date_to}",
                'period': 'range'
            }
        )
    
    def get_top_pages(self, date_from: str, date_to: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get top viewed pages"""
        data = self._make_request(
            'Actions.getPageUrls',
            {
                'date': f"{date_from},{date_to}",
                'period': 'range',
                'flat': 1,
                'filter_limit': limit
            }
        )
        return data if isinstance(data, list) else []
    
    def get_entry_pages(self, date_from: str, date_to: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get main entry pages"""
        data = self._make_request(
            'Actions.getEntryPageUrls',
            {
                'date': f"{date_from},{date_to}",
                'period': 'range',
                'flat': 1,
                'filter_limit': limit
            }
        )
        return data if isinstance(data, list) else []
    
    def get_referrers(self, date_from: str, date_to: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get main traffic sources"""
        data = self._make_request(
            'Referrers.getReferrerType',
            {
                'date': f"{date_from},{date_to}",
                'period': 'range',
                'filter_limit': limit
            }
        )
        return data if isinstance(data, list) else []
    
    def get_complete_stats(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get all statistics for a given period"""
        try:
            # Get overview data
            overview = self.get_visitors_overview(date_from, date_to)
            
            # Get additional data
            top_pages = self.get_top_pages(date_from, date_to)
            entry_pages = self.get_entry_pages(date_from, date_to)
            referrers = self.get_referrers(date_from, date_to)
            
            # Process overview data with safe defaults
            if not overview or 'nb_uniq_visitors' not in overview:
                logger.warning(f"Invalid overview data from Matomo API for period {date_from} to {date_to}")
                overview = {}
            
            return {
                'unique_visitors': overview.get('nb_uniq_visitors', 0),
                'new_visits_percentage': float(overview.get('bounce_rate', '0').rstrip('%')),
                'average_duration': int(overview.get('avg_time_on_site', 0)),
                'bounce_rate_percentage': float(overview.get('bounce_rate', '0').rstrip('%')),
                'page_views': overview.get('nb_pageviews', 0),
                'visitors_per_page': float(overview.get('nb_pageviews', 0)) / max(float(overview.get('nb_uniq_visitors', 1)), 1),
                'top_pages': [
                    {
                        'url': page.get('label', ''),
                        'views': page.get('nb_pageviews', 0),
                        'unique_views': page.get('nb_uniq_pageviews', 0)
                    }
                    for page in top_pages[:3]
                ],
                'main_entry_pages': [
                    {
                        'url': page.get('label', ''),
                        'entries': page.get('entry_nb_visits', 0),
                        'bounce_rate': page.get('bounce_rate', '0%')
                    }
                    for page in entry_pages[:5]
                ],
                'main_sources': [
                    {
                        'source': source.get('label', ''),
                        'visits': source.get('nb_visits', 0),
                        'percentage': source.get('percent_visits', 0)
                    }
                    for source in referrers[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error fetching complete stats from Matomo: {e}")
            raise
    
    def get_evolution_data(self, current_period: str, previous_period: str) -> Dict[str, float]:
        """Get evolution percentages compared to previous period"""
        try:
            current_data = self.get_visitors_overview(current_period, current_period)
            previous_data = self.get_visitors_overview(previous_period, previous_period)
            
            def calculate_evolution(current: int, previous: int) -> float:
                if previous == 0:
                    return 0.0
                return ((current - previous) / previous) * 100
            
            return {
                'visitors_evolution': calculate_evolution(
                    current_data.get('nb_uniq_visitors', 0),
                    previous_data.get('nb_uniq_visitors', 0)
                ),
                'bounce_rate_evolution': calculate_evolution(
                    float(current_data.get('bounce_rate', '0').rstrip('%')),
                    float(previous_data.get('bounce_rate', '0').rstrip('%'))
                ),
                'page_views_evolution': calculate_evolution(
                    current_data.get('nb_pageviews', 0),
                    previous_data.get('nb_pageviews', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating evolution data: {e}")
            return {
                'visitors_evolution': 0.0,
                'bounce_rate_evolution': 0.0,
                'page_views_evolution': 0.0
            }