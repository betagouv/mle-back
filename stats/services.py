import requests
from decimal import Decimal, InvalidOperation
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

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if isinstance(value, str):
            value = value.rstrip("%")
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_decimal_or_none(value: Any):
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _make_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Make a request to Matomo API"""
        url = f"{self.base_url}/index.php"

        default_params = {
            "module": "API",
            "method": method,
            "idSite": self.site_id,
            "format": "json",
        }

        request_params = {**params, **default_params}

        try:
            response = requests.post(
                url,
                params=request_params,
                data={"token_auth": self.token},
                timeout=30,
            )
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                logger.error("Matomo API returned a non-JSON response for method %s.", method)
                raise RuntimeError("Invalid JSON response from Matomo API.") from exc
        except requests.RequestException as e:
            logger.error(f"Matomo API request failed: {e}")
            raise

    def get_visitors_overview(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get visitors overview data"""
        return self._make_request(
            "VisitsSummary.get",
            {
                "date": f"{date_from},{date_to}",
                "period": "range",
            },
        )

    def get_top_pages(self, date_from: str, date_to: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get top viewed pages"""
        data = self._make_request(
            "Actions.getPageUrls",
            {
                "date": f"{date_from},{date_to}",
                "period": "range",
                "flat": 1,
                "filter_limit": limit,
            },
        )
        return data if isinstance(data, list) else []

    def get_entry_pages(self, date_from: str, date_to: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get main entry pages"""
        data = self._make_request(
            "Actions.getEntryPageUrls",
            {
                "date": f"{date_from},{date_to}",
                "period": "range",
                "flat": 1,
                "filter_limit": limit,
            },
        )
        return data if isinstance(data, list) else []

    def get_referrers(self, date_from: str, date_to: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get main traffic sources"""
        data = self._make_request(
            "Referrers.getReferrerType",
            {
                "date": f"{date_from},{date_to}",
                "period": "range",
                "filter_limit": limit,
            },
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
            if not overview or "nb_uniq_visitors" not in overview:
                logger.warning(f"Invalid overview data from Matomo API for period {date_from} to {date_to}")
                overview = {}

            unique_visitors = self._to_int(overview.get("nb_uniq_visitors"))
            page_views = self._to_int(overview.get("nb_pageviews"))

            return {
                "unique_visitors": unique_visitors,
                "new_visits_percentage": self._to_float(
                    overview.get("new_visits") or overview.get("new_visit_percentage") or 0
                ),
                "average_duration": self._to_int(overview.get("avg_time_on_site")),
                "bounce_rate_percentage": self._to_float(overview.get("bounce_rate")),
                "page_views": page_views,
                "visitors_per_page": page_views / max(unique_visitors, 1),
                "top_pages": [
                    {
                        "url": page.get("label", ""),
                        "views": self._to_int(page.get("nb_pageviews")),
                        "unique_views": self._to_int(page.get("nb_uniq_pageviews")),
                    }
                    for page in top_pages[:3]
                ],
                "main_entry_pages": [
                    {
                        "url": page.get("label", ""),
                        "entries": self._to_int(page.get("entry_nb_visits")),
                        "bounce_rate": self._to_float(page.get("bounce_rate")),
                    }
                    for page in entry_pages[:5]
                ],
                "main_sources": [
                    {
                        "source": source.get("label", ""),
                        "visits": self._to_int(source.get("nb_visits")),
                        "percentage": self._to_float(source.get("percent_visits")),
                    }
                    for source in referrers[:5]
                ],
            }

        except Exception as e:
            logger.error(f"Error fetching complete stats from Matomo: {e}")
            raise

    def get_evolution_data(self, current_period: str, previous_period: str) -> Dict[str, float]:
        """Get evolution percentages compared to previous period"""
        try:
            current_data = self.get_visitors_overview(current_period, current_period)
            previous_data = self.get_visitors_overview(previous_period, previous_period)

            def calculate_evolution(current: float, previous: float) -> float:
                if previous == 0:
                    return 0.0
                return ((current - previous) / previous) * 100

            return {
                "visitors_evolution": calculate_evolution(
                    self._to_int(current_data.get("nb_uniq_visitors")),
                    self._to_int(previous_data.get("nb_uniq_visitors")),
                ),
                "bounce_rate_evolution": calculate_evolution(
                    self._to_float(current_data.get("bounce_rate")),
                    self._to_float(previous_data.get("bounce_rate")),
                ),
                "page_views_evolution": calculate_evolution(
                    self._to_int(current_data.get("nb_pageviews")),
                    self._to_int(previous_data.get("nb_pageviews")),
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating evolution data: {e}")
            return {
                "visitors_evolution": 0.0,
                "bounce_rate_evolution": 0.0,
                "page_views_evolution": 0.0,
            }

    def get_all_events(self, date_from: str, date_to: str) -> list:
        """Get all events broken down by category > action in a single API call"""
        data = self._make_request(
            "Events.getCategory",
            {
                "date": f"{date_from},{date_to}",
                "period": "range",
                "secondaryDimension": "eventAction",
                "flat": 1,
            },
        )
        if not isinstance(data, list):
            return []

        events = []
        for row in data:
            # flat mode returns "Category - Action" in label, split it
            label = row.get("label", "")
            parts = label.split(" - ", 1)
            category = parts[0] if parts else label
            action = parts[1] if len(parts) > 1 else ""

            events.append(
                {
                    "category": category,
                    "action": action,
                    "nb_events": self._to_int(row.get("nb_events")),
                    "nb_unique_events": self._to_int(row.get("nb_uniq_visitors")),
                    "event_value": self._to_decimal_or_none(row.get("sum_event_value")),
                }
            )
        return events
