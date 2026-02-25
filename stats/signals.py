from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from account.helpers import is_owner


@receiver(user_logged_in)
def track_gestionnaire_login(sender, request, user, **kwargs):
    if not is_owner(user):
        return

    from stats.models import GestionnaireLoginEvent

    GestionnaireLoginEvent.objects.create(
        user=user,
        owner=user.owners.first(),
    )
