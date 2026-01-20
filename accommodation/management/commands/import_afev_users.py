import csv
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

User = get_user_model()


class Command(BaseCommand):
    help = "Import AFEV users from a CSV file (Nom;Mail) and add them to Owners group"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=Path,
            help="Path to the CSV file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without creating users",
        )

    def handle(self, *args, **options):
        csv_file: Path = options["csv_file"]
        dry_run: bool = options["dry_run"]

        if not csv_file.exists():
            raise CommandError(f"File not found: {csv_file}")

        owners_group, _ = Group.objects.get_or_create(name="Owners")

        created = 0
        skipped = 0

        with csv_file.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")

            required_columns = {"Nom", "Mail"}
            if not required_columns.issubset(reader.fieldnames):
                raise CommandError(f"CSV must contain columns: {', '.join(required_columns)}")

            with transaction.atomic():
                for row in reader:
                    full_name = row.get("Nom", "").strip()
                    email = row.get("Mail", "").strip()

                    if not full_name or "@" not in email:
                        self.stdout.write(self.style.WARNING(f"Skipped invalid row: {row}"))
                        skipped += 1
                        continue

                    first_name, last_name = self._split_name(full_name)

                    username = f"{slugify(first_name)}-{slugify(last_name)}-afev"

                    user, is_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                        },
                    )

                    if is_created:
                        user.groups.add(owners_group)
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"Created: {username}"))
                    else:
                        skipped += 1
                        self.stdout.write(f"Exists: {username}")

                if dry_run:
                    self.stdout.write(self.style.WARNING("Dry-run enabled: rolling back"))
                    raise transaction.TransactionManagementError("Dry run rollback")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created: {created}, Skipped: {skipped}"))

    @staticmethod
    def _split_name(full_name: str):
        parts = full_name.replace("\t", " ").split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        return first_name, last_name
