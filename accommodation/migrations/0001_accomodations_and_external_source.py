# Generated by Django 4.2.17 on 2024-12-09 15:24

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Accommodation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=4326, verbose_name="Localisation"
                    ),
                ),
                ("address", models.CharField(max_length=255)),
                ("city", models.CharField(max_length=150)),
                ("postal_code", models.CharField(max_length=5)),
                (
                    "residence_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            (
                                "universitaire-conventionnee",
                                "Résidence Universitaire conventionnée",
                            ),
                            (
                                "sociale-jeunes-actifs",
                                "Résidence sociale Jeunes Actifs",
                            ),
                            ("intergenerationnelle", "Résidence intergénérationnelle"),
                            ("autre", "Autre"),
                            ("jeunes-travailleurs", "Foyer Jeunes Travailleurs"),
                            (
                                "service-universitaire-privee",
                                "Résidence service / Résidence universitaire privée",
                            ),
                            (
                                "mixte-actifs-etudiants",
                                "Résidence mixte jeunes actifs/étudiants",
                            ),
                            ("u-crous", "Cité U / résidence traditionnelle CROUS"),
                            (
                                "hoteliere-sociale",
                                "Résidence Hôtelière à vocation sociale",
                            ),
                            ("ecole", "Résidence d'école"),
                            ("service-logement", "Service Logement"),
                            ("internat", "Internat"),
                            ("foyer-soleil", "Foyer soleil"),
                        ],
                        max_length=100,
                        null=True,
                    ),
                ),
                ("owner_name", models.CharField(blank=True, max_length=150, null=True)),
                ("owner_url", models.CharField(blank=True, max_length=500, null=True)),
                ("nb_total_apartments", models.IntegerField(blank=True, null=True)),
                (
                    "nb_accessible_apartments",
                    models.IntegerField(blank=True, null=True),
                ),
                ("nb_coliving_apartments", models.IntegerField(blank=True, null=True)),
                ("nb_t1", models.IntegerField(blank=True, null=True)),
                ("nb_t1_bis", models.IntegerField(blank=True, null=True)),
                ("nb_t2", models.IntegerField(blank=True, null=True)),
                ("nb_t3", models.IntegerField(blank=True, null=True)),
                ("nb_t4_more", models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ExternalSource",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("acceslibre", "Accèslibre"), ("clef", "CLEF")],
                        default="clef",
                        max_length=100,
                        verbose_name="Source",
                    ),
                ),
                (
                    "source_id",
                    models.CharField(max_length=100, verbose_name="Source ID"),
                ),
                ("published", models.BooleanField(default=True)),
                (
                    "accommodation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sources",
                        to="accommodation.accommodation",
                    ),
                ),
            ],
            options={
                "unique_together": {("source", "accommodation")},
            },
        ),
    ]
