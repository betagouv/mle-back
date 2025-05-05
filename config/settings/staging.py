from .base import *  # noqa: F403

DEBUG = False

SITE_NAME = f"[STAGING] {SITE_NAME}"  # noqa: F405
ADMIN_TWO_FACTOR_NAME = SITE_NAME

ALLOWED_HOSTS = [
    "mle-back-staging.osc-secnum-fr1.scalingo.io",
    "test.monlogementetudiant.beta.gouv.fr",
    "localhost:3000",
]

SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

FRONT_SITE_URL = "https://test.monlogementetudiant.beta.gouv.fr/"
AWS_SUFFIX_DIR = "-staging"
