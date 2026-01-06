import environ

from .base import *  # noqa: F403

env = environ.Env()

DEBUG = True
TEST = True
ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False

FRONT_SITE_URL = "http://127.0.0.1:8000"

_gdal = env("GDAL_LIBRARY_PATH", default=None)
_geos = env("GEOS_LIBRARY_PATH", default=None)
if _gdal is not None:
    GDAL_LIBRARY_PATH = _gdal
if _geos is not None:
    GEOS_LIBRARY_PATH = _geos
