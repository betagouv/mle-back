import sentry_sdk

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["mle-back-prod.osc-secnum-fr1.scalingo.io"]

ENVIRONMENT = "production"

SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

BREVO_CONTACT_LIST_ID = 4

FRONT_SITE_URL = "https://monlogementetudiant.beta.gouv.fr"
ADMIN_SITE_URL = "https://mle-back-prod.osc-secnum-fr1.scalingo.io"

if SENTRY_DSN is not None:  # noqa: F405
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        environment="production",
    )
