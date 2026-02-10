from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Max, IntegerField, Min, Q, F
from django.db.models.functions import Greatest, Coalesce, Least


PRICE_FIELDS = [
    "price_max_t1",
    "price_max_t1_bis",
    "price_max_t2",
    "price_max_t3",
    "price_max_t4",
    "price_max_t5",
    "price_max_t6",
    "price_max_t7_more",
    "price_min_t1",
    "price_min_t1_bis",
    "price_min_t2",
    "price_min_t3",
    "price_min_t4",
    "price_min_t5",
    "price_min_t6",
    "price_min_t7_more",
]


def get_comparison_queryset(queryset):
    return queryset.filter(
        Q(price_max_t1__isnull=False)
        | Q(price_max_t1_bis__isnull=False)
        | Q(price_max_t2__isnull=False)
        | Q(price_max_t3__isnull=False)
        | Q(price_max_t4__isnull=False)
        | Q(price_max_t5__isnull=False)
        | Q(price_max_t6__isnull=False)
        | Q(price_max_t7_more__isnull=False)
        | Q(price_min_t1__isnull=False)
        | Q(price_min_t1_bis__isnull=False)
        | Q(price_min_t2__isnull=False)
        | Q(price_min_t3__isnull=False)
        | Q(price_min_t4__isnull=False)
        | Q(price_min_t5__isnull=False)
        | Q(price_min_t6__isnull=False)
        | Q(price_min_t7_more__isnull=False)
    )


def max_price_aggregate(queryset):
    queryset = get_comparison_queryset(queryset)
    greatest_expr = Greatest(
        *[Coalesce(field, 0) for field in PRICE_FIELDS],
        output_field=IntegerField(),
    )

    return queryset.aggregate(max_price=Max(greatest_expr))["max_price"]


def min_price_aggregate(queryset):
    queryset = get_comparison_queryset(queryset)

    # Huge number to avoid NULLs winning the LEAST()
    SENTINEL = 10**9

    least_expr = Least(
        *[Coalesce(F(field), SENTINEL) for field in PRICE_FIELDS],
        output_field=IntegerField(),
    )
    return queryset.aggregate(min_price=Min(least_expr))["min_price"]


class AccommodationSearchListPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        queryset = self.page.paginator.object_list

        max_price = max_price_aggregate(queryset)
        min_price = min_price_aggregate(queryset)

        return Response(
            {
                "count": self.page.paginator.count,
                "page_size": self.get_page_size(self.request),
                "max_price": max_price,
                "min_price": min_price,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
