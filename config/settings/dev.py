import sentry_sdk

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
FRONT_SITE_URL = "http://localhost:8000"

AWS_SUFFIX_DIR = "-dev"


if SENTRY_DSN is not None:  # noqa: F405
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        environment="dev",
    )
