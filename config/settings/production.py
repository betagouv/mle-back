from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["mle-back-prod.osc-secnum-fr1.scalingo.io"]

SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

BREVO_CONTACT_LIST_ID = 4

FRONT_SITE_URL = "https://monlogementetudiant.beta.gouv.fr"
