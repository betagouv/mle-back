from django.db import models


class AccommodationQuerySet(models.QuerySet):
    def online_with_images_first(self):
        return self.filter(published=True).exclude(geom=None).order_by("-images_count")
