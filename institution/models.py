from django.contrib.gis.db import models


class EducationalInstitution(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    geom = models.PointField(null=True, blank=True, verbose_name="Localisation")
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=5)
    academy = models.ForeignKey("territories.Academy", on_delete=models.CASCADE, related_name="institutions")
    website = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.city})"
