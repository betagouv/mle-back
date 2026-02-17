from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from accommodation.services import build_accommodation_export_rows
from accommodation.services import build_postal_code_geo_index
from accommodation.services import export_accommodations_to_xlsx
from accommodation.models import Accommodation
from territories.models import City
from territories.models import Department


class Command(BaseCommand):
    help = "Export all accommodations to an XLSX file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="accommodations_export.xlsx",
            help="Output XLSX file path",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        postal_code_to_geo = build_postal_code_geo_index(
            City.objects.values_list(
                "postal_codes",
                "department__name",
                "department__academy__name",
            )
        )
        departments_by_code = {
            code: (department_name, region_name or "")
            for code, department_name, region_name in Department.objects.values_list(
                "code",
                "name",
                "academy__name",
            )
        }
        rows = build_accommodation_export_rows(
            accommodation_rows=Accommodation.objects.order_by("id").values_list(
                "name",
                "owner__name",
                "nb_total_apartments",
                "postal_code",
                "nb_t1_available",
                "nb_t1_bis_available",
                "nb_t2_available",
                "nb_t3_available",
                "nb_t4_available",
                "nb_t5_available",
                "nb_t6_available",
                "nb_t7_more_available",
            ),
            postal_code_to_geo=postal_code_to_geo,
            departments_by_code=departments_by_code,
        )
        exported_count = export_accommodations_to_xlsx(output_path=output_path, rows=rows)

        self.stdout.write(
            self.style.SUCCESS(f"Export finished: {exported_count} accommodations written to {output_path}")
        )
