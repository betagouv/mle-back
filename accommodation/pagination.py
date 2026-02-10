from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accommodation.pricing import PricingAggregates


class AccommodationSearchListPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        queryset = self.page.paginator.object_list
        pricing_aggregates = PricingAggregates(queryset)
        price_bounds = pricing_aggregates.price_bounds()
        return Response(
            {
                "count": self.page.paginator.count,
                "page_size": self.get_page_size(self.request),
                "max_price": price_bounds["max_price"],
                "min_price": price_bounds["min_price"],
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
