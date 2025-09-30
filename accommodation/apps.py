from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class AccommodationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accommodation"
    verbose_name = gettext_lazy("Accommodation")
