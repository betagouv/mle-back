# Generated by Django 4.2.20 on 2025-05-05 13:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accommodation", "0017_price_min_indexes"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="accommodation",
            name="accommodati_images__5c8955_idx",
        ),
        migrations.AddIndex(
            model_name="accommodation",
            index=models.Index(fields=["published", "-images_count"], name="accommodati_publish_7d5dc3_idx"),
        ),
    ]
