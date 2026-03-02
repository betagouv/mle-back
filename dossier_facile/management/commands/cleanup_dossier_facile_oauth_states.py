from django.core.management.base import BaseCommand

from dossier_facile.services import cleanup_expired_oauth_states


class Command(BaseCommand):
    help = "Delete expired Dossier Facile OAuth states."

    def handle(self, *args, **options):
        deleted_count = cleanup_expired_oauth_states()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} expired Dossier Facile OAuth states."))
