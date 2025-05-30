from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import Distance
from django_filters.rest_framework import FilterSet, filters
from rest_framework.exceptions import ValidationError

from .models import Accommodation


class AccommodationFilter(FilterSet):
    bbox = filters.CharFilter(method="filter_bbox", label="Bounding box")
    is_accessible = filters.BooleanFilter(method="filter_is_accessible", label="Only accessible accommodations")
    has_coliving = filters.BooleanFilter(
        method="filter_has_coliving", label="Only accommodations with coliving apartments"
    )
    center = filters.CharFilter(method="filter_center", label="Center point for radius filtering (lon,lat)")
    price_max = filters.NumberFilter(method="filter_price_max", label="Price max in euros")

    def filter_bbox(self, queryset, name, value):
        try:
            bbox = list(map(float, value.split(",")))
            if len(bbox) != 4:
                raise ValidationError("Invalid bbox format. Should be 'xmin,ymin,xmax,ymax'.")

            polygon = Polygon.from_bbox(bbox)
            return queryset.filter(geom__within=polygon)
        except ValueError:
            raise ValidationError("Invalid bbox format. Coordinates should be numbers.")

    def filter_is_accessible(self, queryset, name, value):
        if value is True:
            return queryset.filter(nb_accessible_apartments__gt=0)
        return queryset

    def filter_has_coliving(self, queryset, name, value):
        if value is True:
            return queryset.filter(nb_coliving_apartments__gt=0)
        return queryset

    def filter_center(self, queryset, name, value):
        try:
            lon, lat = map(float, value.split(","))
            point = Point(lon, lat)
            radius = float(self.data.get("radius") or 10)
            distance = Distance(km=radius)
            return queryset.filter(geom__distance_lte=(point, distance))
        except (ValueError, TypeError):
            raise ValidationError("Invalid center format. Should be 'longitude,latitude'. Radius must be a number.")

    def filter_price_max(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(price_min__isnull=False, price_min__lte=value)

    class Meta:
        model = Accommodation
        fields = []
