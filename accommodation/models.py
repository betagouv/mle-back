from autoslug import AutoSlugField
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from account.models import Owner

from .managers import AccommodationManager


class Accommodation(models.Model):
    RESIDENCE_TYPE_CHOICES = (
        ("universitaire-conventionnee", "Résidence Universitaire conventionnée"),
        ("sociale-jeunes-actifs", "Résidence sociale Jeunes Actifs"),
        ("intergenerationnelle", "Résidence intergénérationnelle"),
        ("autre", "Autre"),
        ("jeunes-travailleurs", "Foyer Jeunes Travailleurs"),
        ("service-universitaire-privee", "Résidence service / Résidence universitaire privée"),
        ("mixte-actifs-etudiants", "Résidence mixte jeunes actifs/étudiants"),
        ("u-crous", "Cité U / résidence traditionnelle CROUS"),
        ("hoteliere-sociale", "Résidence Hôtelière à vocation sociale"),
        ("ecole", "Résidence d'école"),
        ("service-logement", "Service Logement"),
        ("internat", "Internat"),
        ("foyer-soleil", "Foyer soleil"),
    )
    SHARED_OR_PRIVATE = (
        ("shared", "Shared"),
        ("private", "Private"),
    )

    name = models.CharField(max_length=200)
    slug = AutoSlugField(max_length=255, default="", unique=True, populate_from="name")
    geom = models.PointField(null=True, blank=True, verbose_name="Localisation")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=150)
    postal_code = models.CharField(max_length=5)
    residence_type = models.CharField(max_length=100, choices=RESIDENCE_TYPE_CHOICES, null=True, blank=True)
    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, null=True, blank=True, related_name="accommodations")
    nb_total_apartments = models.IntegerField(null=True, blank=True)
    nb_accessible_apartments = models.IntegerField(null=True, blank=True)
    nb_coliving_apartments = models.IntegerField(null=True, blank=True)
    nb_t1 = models.IntegerField(null=True, blank=True)
    nb_t1_bis = models.IntegerField(null=True, blank=True)
    nb_t2 = models.IntegerField(null=True, blank=True)
    nb_t3 = models.IntegerField(null=True, blank=True)
    nb_t4_more = models.IntegerField(null=True, blank=True)
    price_min_t1 = models.IntegerField(null=True, blank=True)
    price_max_t1 = models.IntegerField(null=True, blank=True)
    price_min_t1_bis = models.IntegerField(null=True, blank=True)
    price_max_t1_bis = models.IntegerField(null=True, blank=True)
    price_min_t2 = models.IntegerField(null=True, blank=True)
    price_max_t2 = models.IntegerField(null=True, blank=True)
    price_min_t3 = models.IntegerField(null=True, blank=True)
    price_max_t3 = models.IntegerField(null=True, blank=True)
    price_min_t4_more = models.IntegerField(null=True, blank=True)
    price_max_t4_more = models.IntegerField(null=True, blank=True)
    laundry_room = models.BooleanField(default=False)
    common_areas = models.BooleanField(default=False)
    bike_storage = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    secure_access = models.BooleanField(default=False)
    residence_manager = models.BooleanField(default=False)
    kitchen_type = models.CharField(max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True)
    desk = models.BooleanField(default=False)
    cooking_plates = models.BooleanField(default=False)
    microwave = models.BooleanField(default=False)
    refrigerator = models.BooleanField(default=False)
    bathroom = models.CharField(max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True)
    external_url = models.URLField(max_length=255, null=True, blank=True)
    images = ArrayField(models.BinaryField(), null=True, blank=True)

    published = models.BooleanField(default=True)

    objects = AccommodationManager()

    def __str__(self):
        return f"{self.name} - {self.postal_code} {self.city}"


class ExternalSource(models.Model):
    SOURCE_ACCESLIBRE = "acceslibre"
    SOURCE_CLEF = "clef"
    SOURCE_AGEFO = "agefo"
    SOURCE_ESPACIL = "espacil"
    SOURCE_CHOICES = (
        (SOURCE_ACCESLIBRE, "Accèslibre"),
        (SOURCE_CLEF, "CLEF"),
        (SOURCE_AGEFO, "Agefo"),
        (SOURCE_ESPACIL, "Espacil"),
    )

    accommodation = models.ForeignKey("Accommodation", on_delete=models.CASCADE, related_name="sources")
    source = models.CharField(max_length=100, verbose_name="Source", default=SOURCE_CLEF, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=100, verbose_name="Source ID")

    class Meta:
        unique_together = ("source", "accommodation")

    def __str__(self):
        return f"Source {self.source} - {self.source_id} - for {self.accommodation}"
