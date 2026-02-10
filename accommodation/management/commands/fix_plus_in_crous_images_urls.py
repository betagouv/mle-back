from urllib.parse import urlsplit, urlunsplit
from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from accommodation.models import Accommodation


class Command(BaseCommand):
    help = "Fix Crous image URLs"

    def handle(self, *args, **options):
        accs = Accommodation.objects.filter(images_urls__regex=r"\+")
        self.fix_accommodation_images_urls(accs)

    def _fix_plus_in_urls(self, url: str) -> str:
        """
        Replace raw '+' by '%2B' in URL paths only.
        Avoid touching query params or already-encoded values.
        """
        parts = urlsplit(url)

        # Replace '+' only in the path
        fixed_path = parts.path.replace("+", "%2B")

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                fixed_path,
                parts.query,
                parts.fragment,
            )
        )

    def fix_accommodation_images_urls(self, qs: QuerySet[Accommodation]) -> None:
        total = qs.count()
        fixed = 0

        print(f"Found {total} accommodations with '+' in image URLs")

        for acc in qs.iterator():
            new_urls = []
            changed = False

            for url in acc.images_urls or []:
                fixed_url = self._fix_plus_in_urls(url)
                if fixed_url != url:
                    changed = True
                new_urls.append(fixed_url)

            if changed:
                acc.images_urls = new_urls
                acc.save(update_fields=["images_urls"])
                fixed += 1

        print(f"✔ Fixed {fixed} accommodations")
