# Generated by Django 4.2.17 on 2025-01-21 15:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("territories", "0008_city_slug_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="city",
            name="nb_students",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
