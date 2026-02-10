from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from accommodation.models import Accommodation
from accommodation.services import fix_plus_in_url


class Command(BaseCommand):
    help = "Fix Crous image URLs"

    def handle(self, *args, **options):
        accs = Accommodation.objects.filter(images_urls__regex=r"\+")
        self.fix_accommodation_images_urls(accs)

    def fix_accommodation_images_urls(self, qs: QuerySet[Accommodation]) -> None:
        total = qs.count()
        fixed = 0

        print(f"Found {total} accommodations with '+' in image URLs")

        for acc in qs.iterator():
            new_urls = []
            changed = False

            for url in acc.images_urls or []:
                fixed_url = fix_plus_in_url(url)
                if fixed_url != url:
                    changed = True
                new_urls.append(fixed_url)

            if changed:
                acc.images_urls = new_urls
                acc.save(update_fields=["images_urls"])
                fixed += 1

        print(f"✔ Fixed {fixed} accommodations")
