# Generated by Django 4.2.16 on 2024-12-02 16:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionAnswer",
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
                ("title_fr", models.CharField(max_length=200)),
                ("title_en", models.CharField(max_length=200, blank=True, null=True)),
                ("content_fr", models.TextField()),
                ("content_en", models.TextField(blank=True, null=True)),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="questionanswer",
            name="content_en",
            field=models.TextField(blank=True, null=True),
        ),
    ]
