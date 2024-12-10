from django.contrib.gis.geos import Polygon
from django_filters.rest_framework import FilterSet, filters
from rest_framework.exceptions import ValidationError

from .models import Accommodation


class ZoneFilter(FilterSet):
    bbox = filters.CharFilter(method="filter_bbox", label="Bounding box")

    def filter_bbox(self, queryset, name, value):
        try:
            bbox = list(map(float, value.split(",")))
            if len(bbox) != 4:
                raise ValidationError("Invalid bbox format. Should be 'xmin,ymin,xmax,ymax'.")

            polygon = Polygon.from_bbox(bbox)
            return queryset.filter(geom__within=polygon)
        except ValueError:
            raise ValidationError("Invalid bbox format. Coordinates should be numbers.")

    class Meta:
        model = Accommodation
        fields = []
