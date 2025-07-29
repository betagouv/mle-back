from django.db import models

from .queryset import AccommodationQuerySet


class AccommodationManager(models.Manager):
    def get_queryset(self):
        return AccommodationQuerySet(self.model, using=self._db)

    def online(self):
        return self.get_queryset().filter(published=True)

    def online_with_availibility_first(self):
        return self.get_queryset().online_with_availibility_first()
