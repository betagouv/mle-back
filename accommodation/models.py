from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.template.defaultfilters import slugify
from django.urls import reverse

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
    nb_accessible_apartments = models.IntegerField(null=True, blank=True, db_index=True)
    nb_coliving_apartments = models.IntegerField(null=True, blank=True, db_index=True)
    nb_t1 = models.IntegerField(null=True, blank=True)
    nb_t1_bis = models.IntegerField(null=True, blank=True)
    nb_t2 = models.IntegerField(null=True, blank=True)
    nb_t3 = models.IntegerField(null=True, blank=True)
    nb_t4_more = models.IntegerField(null=True, blank=True)
    price_min = models.IntegerField(null=True, blank=True, db_index=True)
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
    laundry_room = models.BooleanField(default=False, null=True, blank=True)
    common_areas = models.BooleanField(default=False, null=True, blank=True)
    bike_storage = models.BooleanField(default=False, null=True, blank=True)
    parking = models.BooleanField(default=False, null=True, blank=True)
    secure_access = models.BooleanField(default=False, null=True, blank=True)
    residence_manager = models.BooleanField(default=False, null=True, blank=True)
    kitchen_type = models.CharField(max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True)
    desk = models.BooleanField(default=False, null=True, blank=True)
    cooking_plates = models.BooleanField(default=False, null=True, blank=True)
    microwave = models.BooleanField(default=False, null=True, blank=True)
    refrigerator = models.BooleanField(default=False, null=True, blank=True)
    bathroom = models.CharField(max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True)
    external_url = models.URLField(max_length=255, null=True, blank=True)
    images_urls = ArrayField(models.URLField(), null=True, blank=True)
    images_count = models.IntegerField(default=0)

    published = models.BooleanField(default=True)
    available = models.BooleanField(default=True)

    objects = AccommodationManager()

    class Meta:
        indexes = [
            models.Index(fields=["published", "-images_count"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.postal_code} {self.city}"

    def get_absolute_detail_api_url(self):
        return reverse("accommodation-detail", kwargs={"slug": self.slug})

    def get_absolute_url(self):
        return f"{settings.FRONT_SITE_URL}/trouver-un-logement-etudiant/ville/{slugify(self.city)}/{self.slug}"

    def save(self, *args, **kwargs):
        self.images_count = len(self.images_urls or [])
        price_min_fields = [
            self.price_min_t1,
            self.price_min_t1_bis,
            self.price_min_t2,
            self.price_min_t3,
            self.price_min_t4_more,
        ]
        non_null_prices = [p for p in price_min_fields if p is not None]
        self.price_min = min(non_null_prices) if non_null_prices else None
        super().save(*args, **kwargs)


class ExternalSource(models.Model):
    SOURCE_ACCESLIBRE = "acceslibre"
    SOURCE_CLEF = "clef"
    SOURCE_AGEFO = "agefo"
    SOURCE_ESPACIL = "espacil"
    SOURCE_ARPEJ = "arpej"
    SOURCE_STUDEFI = "studefi"
    SOURCE_SOGIMA = "sogima"
    SOURCE_ORNE_HABITAT = "orne-habitat"
    SOURCE_OH_MON_APPART = "oh-mon-appart"
    SOURCE_CHOICES = (
        (SOURCE_ACCESLIBRE, "Accèslibre"),
        (SOURCE_CLEF, "CLEF"),
        (SOURCE_AGEFO, "Agefo"),
        (SOURCE_ESPACIL, "Espacil"),
        (SOURCE_ARPEJ, "Arpej"),
        (SOURCE_STUDEFI, "Studefi"),
        (SOURCE_SOGIMA, "Sogima"),
        (SOURCE_ORNE_HABITAT, "Orne Habitat"),
        (SOURCE_OH_MON_APPART, "Oh Mon Appart"),
    )

    accommodation = models.ForeignKey("Accommodation", on_delete=models.CASCADE, related_name="sources")
    source = models.CharField(max_length=100, verbose_name="Source", default=SOURCE_CLEF, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=100, verbose_name="Source ID", null=True, blank=True)

    class Meta:
        unique_together = ("source", "accommodation")

    def __str__(self):
        return f"Source {self.source} - {self.source_id} - for {self.accommodation}"
