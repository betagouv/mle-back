from functools import reduce
from operator import or_
from django.db.models import Case, Max, IntegerField, Min, Q, F, When, Value
from django.db.models.functions import Greatest, Least


PRICE_MIN_FIELDS = [
    "price_min_t1",
    "price_min_t1_bis",
    "price_min_t2",
    "price_min_t3",
    "price_min_t4",
    "price_min_t5",
    "price_min_t6",
    "price_min_t7_more",
]

PRICE_MAX_FIELDS = [
    "price_max_t1",
    "price_max_t1_bis",
    "price_max_t2",
    "price_max_t3",
    "price_max_t4",
    "price_max_t5",
    "price_max_t6",
    "price_max_t7_more",
]

ALL_PRICE_FIELDS = PRICE_MIN_FIELDS + PRICE_MAX_FIELDS


def _has_any_price_q():
    return reduce(
        or_,
        (Q(**{f"{field}__isnull": False}) & Q(**{f"{field}__gt": 0}) for field in ALL_PRICE_FIELDS),
    )


SENTINEL_MAX = 0
SENTINEL_MIN = 10**9


def _greatest_price_expr(fields):
    return Greatest(
        *[
            Case(
                When(**{f"{field}__gt": 0}, then=F(field)),
                default=Value(0),
                output_field=IntegerField(),
            )
            for field in fields
        ],
        output_field=IntegerField(),
    )


def _least_price_expr(fields):
    return Least(
        *[
            Case(
                When(**{f"{field}__gt": 0}, then=F(field)),
                default=Value(SENTINEL_MIN),
                output_field=IntegerField(),
            )
            for field in fields
        ],
        output_field=IntegerField(),
    )


class PricingAggregates:
    def __init__(self, queryset):
        self.queryset = queryset.filter(_has_any_price_q()).only(*ALL_PRICE_FIELDS)

    def price_bounds(self):
        """
        Returns global min and max price across all accommodations.
        """
        return self.queryset.aggregate(
            max_price=Max(_greatest_price_expr(ALL_PRICE_FIELDS)),
            min_price=Min(_least_price_expr(ALL_PRICE_FIELDS)),
        )
