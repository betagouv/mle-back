from django.db import models
from django.db.models import F, Value
from django.db.models.expressions import Func
from django.db.models.functions import Coalesce


class AccommodationQuerySet(models.QuerySet):
    def online_with_images_first(self):
        return (
            self.filter(published=True)
            .exclude(geom=None)
            .annotate(
                image_count=Coalesce(
                    Func(F("images"), function="CARDINALITY", output_field=models.IntegerField()),
                    Value(0),
                )
            )
            .order_by("-image_count")
        )
