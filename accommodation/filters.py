from django.db.models import Q
from django_filters.rest_framework import filters

from accommodation.models import Accommodation
from common.filters import BaseFilter


class AccommodationFilter(BaseFilter):
    is_accessible = filters.BooleanFilter(method="filter_is_accessible", label="Only accessible accommodations")
    only_with_availibility = filters.BooleanFilter(
        method="filter_only_with_availibility", label="Only available accommodations"
    )
    has_coliving = filters.BooleanFilter(
        method="filter_has_coliving", label="Only accommodations with coliving apartments"
    )
    price_max = filters.NumberFilter(method="filter_price_max", label="Price max in euros")

    def filter_is_accessible(self, queryset, name, value):
        if value is True:
            return queryset.filter(nb_accessible_apartments__gt=0)
        return queryset

    def filter_only_with_availibility(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                Q(nb_t1_available__gt=0)
                | Q(nb_t1_bis_available__gt=0)
                | Q(nb_t2_available__gt=0)
                | Q(nb_t3_available__gt=0)
                | Q(nb_t4_more_available__gt=0)
            )
        return queryset

    def filter_has_coliving(self, queryset, name, value):
        if value is True:
            return queryset.filter(nb_coliving_apartments__gt=0)
        return queryset

    def filter_price_max(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(price_min__isnull=False, price_min__lte=value)

    class Meta:
        model = Accommodation
        fields = []
