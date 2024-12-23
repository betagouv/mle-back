from .base import *  # noqa: F403

DEBUG = False

SITE_NAME = f"[STAGING] {SITE_NAME}"  # noqa: F405
ALLOWED_HOSTS = ["mle-back-staging.osc-secnum-fr1.scalingo.io"]

SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
