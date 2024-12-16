# Generated by Django 4.2.17 on 2024-12-16 09:25

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accommodation", "0004_accommodation_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accommodation",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                default="",
                editable=False,
                max_length=255,
                populate_from="name",
                unique=True,
            ),
        ),
    ]