# Generated by Django 4.2.20 on 2025-03-24 16:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accommodation", "0011_accommodation_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accommodation",
            name="bike_storage",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="common_areas",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="cooking_plates",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="desk",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="laundry_room",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="microwave",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="parking",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="refrigerator",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="residence_manager",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="secure_access",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
