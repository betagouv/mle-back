from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy

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

    name = models.CharField(max_length=200, verbose_name=gettext_lazy("Name"))
    slug = AutoSlugField(max_length=255, default="", unique=True, populate_from="name")
    description = models.TextField(null=True, blank=True, verbose_name=gettext_lazy("Description"))
    geom = models.PointField(null=True, blank=True, verbose_name=gettext_lazy("Location"))
    address = models.CharField(max_length=255, verbose_name=gettext_lazy("Address"))
    city = models.CharField(max_length=150, verbose_name=gettext_lazy("City"))
    postal_code = models.CharField(max_length=5, verbose_name=gettext_lazy("Postal code"))
    residence_type = models.CharField(
        max_length=100,
        choices=RESIDENCE_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("Residence type"),
    )
    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, null=True, blank=True, related_name="accommodations")
    nb_total_apartments = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Total number of apartments")
    )
    nb_accessible_apartments = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name=gettext_lazy("Number of accessible apartments")
    )
    nb_coliving_apartments = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name=gettext_lazy("Number of coliving apartments")
    )
    nb_t1 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Number of T1"))
    nb_t1_available = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Number of available T1")
    )
    nb_t1_bis = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Number of T1 bis"))
    nb_t1_bis_available = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Number of available T1 bis")
    )
    nb_t2 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Number of T2"))
    nb_t2_available = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Number of available T2")
    )
    nb_t3 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Number of T3"))
    nb_t3_available = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Number of available T3")
    )
    nb_t4_more = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Number of T4"))
    nb_t4_more_available = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Number of available T4")
    )
    price_min = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name=gettext_lazy("Minimum price")
    )
    price_min_t1 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Minimum price for T1"))
    price_max_t1 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Maximum price for T1"))
    price_min_t1_bis = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Minimum price for T1 bis")
    )
    price_max_t1_bis = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Maximum price for T1 bis")
    )
    price_min_t2 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Minimum price for T2"))
    price_max_t2 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Maximum price for T2"))
    price_min_t3 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Minimum price for T3"))
    price_max_t3 = models.PositiveIntegerField(null=True, blank=True, verbose_name=gettext_lazy("Maximum price for T3"))
    price_min_t4_more = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Minimum price for T4")
    )
    price_max_t4_more = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=gettext_lazy("Maximum price for T4")
    )
    laundry_room = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Laundry room"))
    common_areas = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Common areas"))
    bike_storage = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Bike storage"))
    parking = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Parking"))
    secure_access = models.BooleanField(
        default=False, null=True, blank=True, verbose_name=gettext_lazy("Secure access")
    )
    residence_manager = models.BooleanField(
        default=False, null=True, blank=True, verbose_name=gettext_lazy("Residence manager")
    )
    kitchen_type = models.CharField(
        max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True, verbose_name=gettext_lazy("Kitchen type")
    )
    desk = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Desk"))
    cooking_plates = models.BooleanField(
        default=False, null=True, blank=True, verbose_name=gettext_lazy("Cooking plates")
    )
    microwave = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Microwave"))
    refrigerator = models.BooleanField(default=False, null=True, blank=True, verbose_name=gettext_lazy("Refrigerator"))
    bathroom = models.CharField(
        max_length=50, choices=SHARED_OR_PRIVATE, null=True, blank=True, verbose_name=gettext_lazy("Bathroom")
    )
    accept_waiting_list = models.BooleanField(
        default=False, null=True, blank=True, verbose_name=gettext_lazy("Accept waiting list")
    )
    external_url = models.URLField(max_length=255, null=True, blank=True)
    images_urls = ArrayField(models.URLField(), null=True, blank=True)
    images_count = models.PositiveIntegerField(default=0)

    published = models.BooleanField(default=True, verbose_name=gettext_lazy("Published"))
    available = models.BooleanField(default=True, verbose_name=gettext_lazy("Available"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccommodationManager()

    class Meta:
        indexes = [
            models.Index(fields=["published", "-images_count"]),
        ]
        verbose_name = gettext_lazy("Accommodation")
        verbose_name_plural = gettext_lazy("Accommodations")

    def __str__(self):
        return f"{self.name} - {self.postal_code} {self.city}"

    def get_absolute_detail_api_url(self):
        return reverse("accommodation-detail", kwargs={"slug": self.slug})

    def get_absolute_url(self):
        return f"{settings.FRONT_SITE_URL}/trouver-un-logement-etudiant/ville/{slugify(self.city)}/{self.slug}"

    def save(self, *args, **kwargs):
        self.clean()
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

        self.nb_total_apartments = sum(
            [
                int(self.nb_t1 or 0),
                int(self.nb_t1_bis or 0),
                int(self.nb_t2 or 0),
                int(self.nb_t3 or 0),
                int(self.nb_t4_more or 0),
            ]
        )
        super().save(*args, **kwargs)

    def clean(self):
        for attr_available in [
            "nb_t1_available",
            "nb_t1_bis_available",
            "nb_t2_available",
            "nb_t3_available",
            "nb_t4_more_available",
        ]:
            field_available = getattr(self, attr_available)
            field_stock = getattr(self, attr_available.replace("_available", ""))
            if field_available is not None and field_stock is not None and field_available > field_stock:
                field_available = field_stock
                setattr(self, attr_available, field_available)

        reserved_slugs = {"my"}
        if self.slug in reserved_slugs:
            raise ValidationError({"slug": f"Reserved slug '{self.slug}'."})


class ExternalSource(models.Model):
    SOURCE_ACCESLIBRE = "acceslibre"
    SOURCE_CLEF = "clef"
    SOURCE_AGEFO = "agefo"
    SOURCE_ESPACIL = "espacil"
    SOURCE_ARPEJ = "arpej"
    SOURCE_STUDEFI = "studefi"
    SOURCE_SOGIMA = "sogima"
    SOURCE_ORNE_HABITAT = "orne-habitat"
    SOURCE_TARN_HABITAT = "tarn-habitat"
    SOURCE_OH_MON_APPART = "oh-mon-appart"
    SOURCE_EVOLEA = "evolea"
    SOURCE_PARTELIOS = "partelios"
    SOURCE_SEQENS = "seqens"
    SOURCE_PARME = "parme"
    SOURCE_BMH = "bmh"
    SOURCE_NANTAISE = "nantaise"
    SOURCE_VENDEE = "vendee"
    SOURCE_FRANCE_LOIRE = "france-loire"
    SOURCE_HABELLIS = "habellis"
    SOURCE_CROUS = "crous"
    SOURCE_ESCALE_OUEST = "escale-ouest"
    SOURCE_APHEEN = "apheen"
    SOURCE_PODELIHA = "podeliha"
    SOURCE_MGEL = "mgel"
    SOURCE_EST_HABITAT = "est-habitat"
    SOURCE_PROMOLOGIS = "promologis"
    SOURCE_CHOICES = (
        (SOURCE_ACCESLIBRE, "Accèslibre"),
        (SOURCE_CLEF, "CLEF"),
        (SOURCE_AGEFO, "Agefo"),
        (SOURCE_ESPACIL, "Espacil"),
        (SOURCE_ARPEJ, "Arpej"),
        (SOURCE_STUDEFI, "Studefi"),
        (SOURCE_SOGIMA, "Sogima"),
        (SOURCE_ORNE_HABITAT, "Orne Habitat"),
        (SOURCE_TARN_HABITAT, "Tarn Habitat"),
        (SOURCE_OH_MON_APPART, "Oh Mon Appart"),
        (SOURCE_EVOLEA, "Evolea"),
        (SOURCE_PARTELIOS, "Partelios"),
        (SOURCE_SEQENS, "Seqens/Adlis"),
        (SOURCE_PARME, "Parme"),
        (SOURCE_BMH, "Brest Métropole Habitat"),
        (SOURCE_NANTAISE, "Nantaise d'habitation"),
        (SOURCE_VENDEE, "Vendée logement"),
        (SOURCE_FRANCE_LOIRE, "France Loire"),
        (SOURCE_HABELLIS, "Habellis"),
        (SOURCE_CROUS, "Crous"),
        (SOURCE_ESCALE_OUEST, "Escale Ouest"),
        (SOURCE_APHEEN, "Apheen"),
        (SOURCE_PODELIHA, "Podeliha"),
        (SOURCE_MGEL, "MGEL"),
        (SOURCE_EST_HABITAT, "Est Habitat"),
        (SOURCE_PROMOLOGIS, "Promologis"),
    )

    accommodation = models.ForeignKey("Accommodation", on_delete=models.CASCADE, related_name="sources")
    source = models.CharField(max_length=100, verbose_name="Source", default=SOURCE_CLEF, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=100, verbose_name="Source ID", null=True, blank=True)

    class Meta:
        unique_together = ("source", "accommodation")
        verbose_name = gettext_lazy("External source")
        verbose_name_plural = gettext_lazy("External sources")

    def __str__(self):
        return f"Source {self.source} - {self.source_id} - for {self.accommodation}"
