import json
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from territories.models import Country, Academy, Department, City


class Command(BaseCommand):
    help = "Generate a JSON template for QuestionAnswer completion"

    def handle(self, *args, **kwargs):
        data = []

        for country in Country.objects.all():
            content_type = ContentType.objects.get_for_model(Country)
            data.append(
                {
                    "model": "qa.questionanswer",
                    "pk": None,
                    "fields": {
                        "title_fr": "",
                        "title_en": "",
                        "content_fr": "",
                        "content_en": "",
                        "content_type": content_type.id,
                        "object_id": country.pk,
                    },
                    "info": {"territory_type": "Country", "name": country.name},
                }
            )

        for academy in Academy.objects.all():
            content_type = ContentType.objects.get_for_model(Academy)
            data.append(
                {
                    "model": "qa.questionanswer",
                    "pk": None,
                    "fields": {
                        "title_fr": "",
                        "title_en": "",
                        "content_fr": "",
                        "content_en": "",
                        "content_type": content_type.id,
                        "object_id": academy.pk,
                    },
                    "info": {"territory_type": "Academy", "name": academy.name},
                }
            )

        for department in Department.objects.all():
            content_type = ContentType.objects.get_for_model(Department)
            data.append(
                {
                    "model": "qa.questionanswer",
                    "pk": None,
                    "fields": {
                        "title_fr": "",
                        "title_en": "",
                        "content_fr": "",
                        "content_en": "",
                        "content_type": content_type.id,
                        "object_id": department.pk,
                    },
                    "info": {"territory_type": "Department", "name": department.name},
                }
            )

        for city in City.objects.all():
            content_type = ContentType.objects.get_for_model(City)
            data.append(
                {
                    "model": "qa.questionanswer",
                    "pk": None,
                    "fields": {
                        "title_fr": "",
                        "title_en": "",
                        "content_fr": "",
                        "content_en": "",
                        "content_type": content_type.id,
                        "object_id": city.pk,
                    },
                    "info": {"territory_type": "City", "name": city.name},
                }
            )

        output_file = "qa_fixtures_template.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(f"JSON file generated: {output_file}")
