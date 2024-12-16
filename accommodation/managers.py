from django.contrib.gis.db import models


class AccommodationManager(models.Manager):
    def online(self):
        return self.filter(published=True).exclude(geom__isnull=True)
