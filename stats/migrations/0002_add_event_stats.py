# Generated migration for EventStats model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("stats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventStats",
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
                ("category", models.CharField(max_length=100)),
                ("action", models.CharField(max_length=200)),
                ("nb_events", models.IntegerField(default=0)),
                ("nb_unique_events", models.IntegerField(default=0)),
                (
                    "event_value",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Event Statistics",
                "verbose_name_plural": "Event Statistics",
                "ordering": ["-date_from", "-nb_events"],
            },
        ),
        migrations.AddIndex(
            model_name="eventstats",
            index=models.Index(
                fields=["period", "date_from"],
                name="stats_event_period_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="eventstats",
            index=models.Index(
                fields=["category", "action"],
                name="stats_event_cat_action_idx",
            ),
        ),
    ]
