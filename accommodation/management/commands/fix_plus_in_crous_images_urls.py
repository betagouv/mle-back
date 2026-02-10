from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from accommodation.models import Accommodation
from accommodation.services import fix_plus_in_url


class Command(BaseCommand):
    help = "Fix Crous image URLs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving",
        )

    def handle(self, *args, **options):
        accs = Accommodation.objects.filter(images_urls__regex=r"\+")
        self.fix_accommodation_images_urls(accs, dry_run=options["dry_run"])

    def fix_accommodation_images_urls(self, qs: QuerySet[Accommodation], *, dry_run: bool = False) -> None:
        total = qs.count()
        fixed = 0

        self.stdout.write(f"Found {total} accommodations with '+' in image URLs")

        for acc in qs.iterator():
            new_urls = []
            changed = False

            for url in acc.images_urls or []:
                fixed_url = fix_plus_in_url(url)
                if fixed_url != url:
                    changed = True
                new_urls.append(fixed_url)

            if changed:
                if not dry_run:
                    acc.images_urls = new_urls
                    acc.save(update_fields=["images_urls"])
                fixed += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run: {fixed} accommodations would be fixed"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} accommodations"))
