import os

from django.core.management.base import BaseCommand
from django.db.models import Func, Value

from accommodation.crous_prices_service import import_crous_prices
from accommodation.models import Accommodation


class Command(BaseCommand):
    help = "Import Crous prices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving",
        )

        parser.add_argument(
            "--source",
            type=str,
            help="Source of the data",
            default="crous",
        )

    def handle(self, *args, **options):
        csv_file_path = options["source"]

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        dry_run = options["dry_run"]
        result = import_crous_prices(
            csv_file_path=csv_file_path,
            find_accommodation=self._find_accommodation_by_name,
            apply_prices=self._update_accommodation,
            dry_run=dry_run,
        )

        for name in result.missing_accommodations:
            self.stderr.write(self.style.WARNING(f"Accommodation not found: {name}, skipping"))

        for unmapped_type in result.unmapped_types:
            self.stderr.write(self.style.WARNING(f"Non mapped type: {unmapped_type}"))

        self.stdout.write(self.style.SUCCESS(f"Import finished: {result.total_updated} residences updated"))

    def _find_accommodation_by_name(self, name: str) -> Accommodation | None:
        return (
            Accommodation.objects.annotate(unaccent_name=Func("name", function="unaccent"))
            .filter(unaccent_name__iexact=Func(Value(name), function="unaccent"))
            .first()
        )

    def _update_accommodation(self, acc_instance: Accommodation, vals: dict, dry_run: bool) -> None:
        for key, value in vals.items():
            setattr(acc_instance, key, value)
        if not dry_run:
            acc_instance.save()
