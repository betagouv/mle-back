from django.db import models
from django.db.models import F
from django.db.models.functions import Coalesce


class AccommodationQuerySet(models.QuerySet):
    def online_with_availibility_first(self):
        return (
            self.filter(published=True)
            .exclude(geom=None)
            .annotate(
                total_available=(
                    Coalesce(F("nb_t1_available"), 0)
                    + Coalesce(F("nb_t1_bis_available"), 0)
                    + Coalesce(F("nb_t2_available"), 0)
                    + Coalesce(F("nb_t3_available"), 0)
                    + Coalesce(F("nb_t4_more_available"), 0)
                )
            )
            .order_by("-total_available")
        )
