# Generated migration for Stats model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Stats",
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
                    "period",
                    models.CharField(
                        choices=[("weekly", "Weekly"), ("monthly", "Monthly")],
                        max_length=10,
                    ),
                ),
                ("date_from", models.DateField()),
                ("date_to", models.DateField()),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("unique_visitors", models.IntegerField()),
                (
                    "new_visits_percentage",
                    models.DecimalField(decimal_places=2, max_digits=5),
                ),
                ("average_duration", models.IntegerField()),
                (
                    "visitors_evolution_percentage",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=6, null=True
                    ),
                ),
                (
                    "bounce_rate_percentage",
                    models.DecimalField(decimal_places=2, max_digits=5),
                ),
                (
                    "bounce_rate_evolution_percentage",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=6, null=True
                    ),
                ),
                ("page_views", models.IntegerField()),
                (
                    "visitors_per_page",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "page_views_evolution_percentage",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=6, null=True
                    ),
                ),
                ("top_pages", models.JSONField(default=list)),
                ("main_entry_pages", models.JSONField(default=list)),
                ("main_sources", models.JSONField(default=list)),
            ],
            options={
                "verbose_name": "Website Statistics",
                "verbose_name_plural": "Website Statistics",
                "ordering": ["-date_from"],
            },
        ),
        migrations.AddIndex(
            model_name="stats",
            index=models.Index(fields=["period", "date_from"], name="stats_stats_period_5c5b69_idx"),
        ),
        migrations.AddIndex(
            model_name="stats",
            index=models.Index(fields=["created_at"], name="stats_stats_created_6f1d3e_idx"),
        ),
    ]