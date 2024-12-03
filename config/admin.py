from django.conf import settings
from django.contrib import admin

admin.site.site_title = f"Administration de {settings.SITE_NAME}"
admin.site.site_header = f"Gestion de {settings.SITE_NAME}"
admin.site.index_title = f"Bienvenue sur l'administration de {settings.SITE_NAME}"
