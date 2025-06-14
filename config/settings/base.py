import os
from pathlib import Path

import environ

env = environ.Env()

DEBUG = False
TEST = False

SITE_NAME = "MLE"
ADMIN_TWO_FACTOR_NAME = SITE_NAME

BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "admin_two_factor.apps.TwoStepVerificationConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "territories",
    "qa",
    "account",
    "accommodation",
    "django_admin_logs",
    "django_summernote",
    "drf_spectacular",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "account.middleware.AdminLoginRedirectMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

database_url = os.environ.get("DATABASE_URL", "postgres://jde:jde@localhost/jde")
DATABASES = {
    "default": env.db(),
}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "fr-fr"
LANGUAGES = [
    ("fr", "French"),
    ("en", "English"),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = "fr"
MODELTRANSLATION_LANGUAGES = ("fr", "en")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("fr",)

USE_I18N = True

TIME_ZONE = "UTC"

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "staticfiles"))
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.CustomPageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 30,
}

SPECTACULAR_SETTINGS = {
    "TITLE": f"{SITE_NAME} API",
    "DESCRIPTION": "",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

DJANGO_ADMIN_LOGS_IGNORE_UNCHANGED = True


# OMOGEN API
OMOGEN_API_API_KEY = env("OMOGEN_API_API_KEY")
OMOGEN_API_CLIENT_ID = env("OMOGEN_API_CLIENT_ID")
OMOGEN_API_CLIENT_SECRET = env("OMOGEN_API_CLIENT_SECRET")
OMOGEN_API_HOST = env("OMOGEN_API_HOST")
OMOGEN_API_AUTH_PATH = env("OMOGEN_API_AUTH_PATH")
OMOGEN_API_CLEF_APP_NAME = env("OMOGEN_API_CLEF_APP_NAME")

# BREVO API
BREVO_API_KEY = env("BREVO_API_KEY")
BREVO_CONTACT_LIST_ID = 3

# IBAIL API
IBAIL_API_AUTH_KEY = env("IBAIL_API_AUTH_KEY")
IBAIL_API_AUTH_SECRET = env("IBAIL_API_AUTH_SECRET")
IBAIL_API_HOST = env("IBAIL_API_HOST")


# OVH S3 settings (keeping AWS prefix for compatibility)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", default="path")
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", default="public-read")
AWS_SUFFIX_DIR = ""
AWS_S3_PUBLIC_BASE_URL = env("AWS_S3_PUBLIC_BASE_URL")
