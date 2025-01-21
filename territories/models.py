from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField


class Territory(models.Model):
    name = models.CharField(max_length=200)
    boundary = models.MultiPolygonField(null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def get_content_type(self):
        return ContentType.objects.get_for_model(self.__class__)

    def get_bbox(self):
        if self.boundary:
            extent = self.boundary.extent
            return {
                "xmin": extent[0],
                "ymin": extent[1],
                "xmax": extent[2],
                "ymax": extent[3],
            }
        return None


class Country(Territory):
    boundary = None

    def __str__(self):
        return self.name


class Academy(Territory):
    def __str__(self):
        return self.name


class Department(Territory):
    code = models.CharField(max_length=3, unique=True)
    academy = models.ForeignKey(Academy, on_delete=models.CASCADE, related_name="departments")

    def __str__(self):
        return f"{self.name} ({self.code})"


class City(Territory):
    postal_codes = ArrayField(
        models.CharField(max_length=5),
        default=list,
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="cities")
    insee_code = models.CharField(max_length=5, null=True, blank=True)
    epci_code = models.CharField(max_length=9, null=True, blank=True)
    popular = models.BooleanField(default=False)
    population = models.IntegerField(null=True, blank=True)
    average_income = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({', '.join(self.postal_codes)})"
