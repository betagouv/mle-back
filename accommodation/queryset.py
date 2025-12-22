from django.db import models
from django.db.models import BooleanField, Case, F, IntegerField, Q, Value, When
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
                    + Coalesce(F("nb_t4_available"), 0)
                    + Coalesce(F("nb_t5_available"), 0)
                    + Coalesce(F("nb_t6_available"), 0)
                    + Coalesce(F("nb_t7_available"), 0)
                ),
                unknown_availibility=Case(
                    When(
                        Q(nb_t1_available__isnull=True)
                        & Q(nb_t1_bis_available__isnull=True)
                        & Q(nb_t2_available__isnull=True)
                        & Q(nb_t3_available__isnull=True)
                        & Q(nb_t4_available__isnull=True)
                        & Q(nb_t5_available__isnull=True)
                        & Q(nb_t6_available__isnull=True)
                        & Q(nb_t7_available__isnull=True),
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            .annotate(
                priority=Case(
                    When(total_available__gt=0, then=Value(1)),
                    When(total_available=0, accept_waiting_list=True, unknown_availibility=False, then=Value(2)),
                    When(unknown_availibility=True, accept_waiting_list=True, then=Value(3)),
                    When(unknown_availibility=True, accept_waiting_list=False, then=Value(4)),
                    When(total_available=0, accept_waiting_list=False, unknown_availibility=False, then=Value(5)),
                    default=Value(6),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority", "-total_available")
        )
