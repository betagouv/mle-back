from django.contrib.gis.geos import Polygon
from django_filters.rest_framework import FilterSet, filters
from rest_framework.exceptions import ValidationError

from .models import Accommodation


class AccommodationFilter(FilterSet):
    bbox = filters.CharFilter(method="filter_bbox", label="Bounding box")
    is_accessible = filters.BooleanFilter(method="filter_is_accessible", label="Only accessible accommodations")

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

    class Meta:
        model = Accommodation
        fields = []
