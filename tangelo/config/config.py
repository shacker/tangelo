import base64
import os
from pathlib import Path

from goodconf import Field, GoodConf


PROJECT_ROOT = Path(__file__).parents[1].resolve()


class AppConfig(GoodConf):
    """Configuration for Greenhouse. Attempts to pull environment variables from
    the running instance and store them as Django settings for use in code."""

    ALLOWED_HOSTS = Field(default=["*"])
    DEBUG = Field(default=False, help="Toggle debugging.")
    DATABASE_URL = Field(
        default="postgres://localhost:5432/greenhouse", help="Database connection."
    )
    # REDIS_URL = Field(default="redis://127.0.0.1:6379")
    # REDIS_PREFIX = Field(default="green")
    SECRET_KEY: str = Field(
        initial=lambda: base64.b64encode(os.urandom(60)).decode(),
        description="Used for cryptographic signing. "
        "https://docs.djangoproject.com/en/2.0/ref/settings/#secret-key",
    )
    MEDIA_ROOT = Field(default=str(PROJECT_ROOT / "media"))
    STATIC_ROOT = Field(default=str(PROJECT_ROOT / "staticfiles"))

    CACHE_BACKEND = Field(default="django.core.cache.backends.redis.RedisCache")
    CACHE_TTL = Field(default=(60 * 60 * 24 * 365))  # One year - cache "permanently" until cleared

    # ES_IRIS_TOKEN = Field(default="", help="Access token issued by Greenhouse to Iris")
    # ES_GH_TOKEN = Field(default="", help="Access token issued by Iris to Greenhouse")

    EMAIL_BACKEND = Field(default="django.core.mail.backends.console.EmailBackend")
    EMAIL_HOST_PASSWORD = Field(default="", help="SMTP email pass")

    FLICKR_API_KEY = Field(default="", help="API key issued by Flickr")
    FLICKR_API_SECRET = Field(default="", help="API secret issued by Flickr")
    FLICKR_USERNAME = Field(default="", help="Flickr username")

    # See table on this page for thumbnail size reference: https://www.flickr.com/services/api/misc.urls.html
    FLICKR_IMAGE_SIZE = Field(default="b", help="Image size for image detail view")
    FLICKR_THUMBNAIL_SIZE = Field(default="n", help="Thumnbail size for categories and images in grids")
    FLICKR_CROPPED_THUMB_SIZE = Field(default="q", help="Cropped square thumnbail size for albums on homepage")

    class Config:
        # Load config from file in GREENHOUSE_CONF env var or `greenhouse.yml` in the cwd
        default_files = [
            "tangelo/config/local.yml",
        ]


config = AppConfig()


def manage_py():
    """Entrypoint for manage.py"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tangelo.config.settings")
    config.django_manage()


def generate_config():
    """Entrypoint for dumping out sample config"""
    print(config.generate_json(LOCAL_DEV=True, DEBUG=True, LOG_LEVEL="DEBUG"))
