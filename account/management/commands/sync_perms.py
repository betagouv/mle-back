from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from account.permissions import GROUPS_PERMISSIONS


class Command(BaseCommand):
    help = "Groups and permissions synchro."

    def handle(self, *args, **options):
        for group_name, data in GROUPS_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)

            perms = []
            for perm_codename in data.get("permissions", []):
                try:
                    perm = Permission.objects.get(codename=perm_codename)
                    perms.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission '{perm_codename}' not found."))

            group.permissions.set(perms)
            group.save()

            self.stdout.write(self.style.SUCCESS(f"Group '{group_name}' synchronized ({len(perms)} permissions)"))
