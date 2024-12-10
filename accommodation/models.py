from django.contrib.gis.db import models


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

    name = models.CharField(max_length=200)
    geom = models.PointField(null=True, blank=True, verbose_name="Localisation")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=150)
    postal_code = models.CharField(max_length=5)
    residence_type = models.CharField(max_length=100, choices=RESIDENCE_TYPE_CHOICES, null=True, blank=True)
    owner_name = models.CharField(max_length=150, null=True, blank=True)
    owner_url = models.CharField(max_length=500, null=True, blank=True)
    nb_total_apartments = models.IntegerField(null=True, blank=True)
    nb_accessible_apartments = models.IntegerField(null=True, blank=True)
    nb_coliving_apartments = models.IntegerField(null=True, blank=True)
    nb_t1 = models.IntegerField(null=True, blank=True)
    nb_t1_bis = models.IntegerField(null=True, blank=True)
    nb_t2 = models.IntegerField(null=True, blank=True)
    nb_t3 = models.IntegerField(null=True, blank=True)
    nb_t4_more = models.IntegerField(null=True, blank=True)
    published = models.BooleanField(default=True)


class ExternalSource(models.Model):
    SOURCE_ACCESLIBRE = "acceslibre"
    SOURCE_CLEF = "clef"
    SOURCE_CHOICES = (
        (SOURCE_ACCESLIBRE, "Accèslibre"),
        (SOURCE_CLEF, "CLEF"),
    )

    accommodation = models.ForeignKey("Accommodation", on_delete=models.CASCADE, related_name="sources")
    source = models.CharField(max_length=100, verbose_name="Source", default=SOURCE_CLEF, choices=SOURCE_CHOICES)
    source_id = models.CharField(max_length=100, verbose_name="Source ID")

    class Meta:
        unique_together = ("source", "accommodation")
