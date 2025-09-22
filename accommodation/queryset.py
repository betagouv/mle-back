from django.db import models
from django.db.models import Case, F, IntegerField, Value, When
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
            .annotate(
                priority=Case(
                    When(total_available__gt=0, then=Value(1)),
                    When(total_available=0, accept_waiting_list=True, then=Value(2)),
                    When(total_available__isnull=True, accept_waiting_list=True, then=Value(3)),
                    When(total_available__isnull=True, accept_waiting_list=False, then=Value(4)),
                    When(total_available=0, accept_waiting_list=False, then=Value(5)),
                    default=Value(6),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority", "-total_available")
        )
