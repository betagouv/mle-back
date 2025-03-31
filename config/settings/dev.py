from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
FRONT_SITE_URL = "http://localhost:8000"
