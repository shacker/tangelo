import base64
import os
from pathlib import Path

from goodconf import Field, GoodConf

# Make these the same as in main settings:
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppConfig(GoodConf):
    """Pulls environment variables from the running instance
    and stores them as Django settings for use in code."""

    ALLOWED_HOSTS: list[str] = Field(default=["*"])
    DEBUG: bool = Field(default=False, help="Toggle debugging.")
    DATABASE_URL: str = Field(
        default="postgres://localhost:5432/greenhouse", help="Database connection."
    )
    # REDIS_URL = Field(default="redis://127.0.0.1:6379")
    # REDIS_PREFIX = Field(default="green")
    SECRET_KEY: str = Field(
        initial=lambda: base64.b64encode(os.urandom(60)).decode(),
        description="Used for cryptographic signing. "
        "https://docs.djangoproject.com/en/2.0/ref/settings/#secret-key",
    )
    MEDIA_ROOT: str = Field(default=str(BASE_DIR / "media"))
    # STATIC_ROOT: str = Field(default=str(BASE_DIR / "staticfiles"))
    STATIC_ROOT: str = Field(default=os.path.join(PROJECT_ROOT, 'staticfiles'))

    CACHE_BACKEND: str = Field(default="django.core.cache.backends.redis.RedisCache")
    CACHE_TTL: int = Field(default=(60 * 60 * 24 * 365))  # One year - cache "permanently" until cleared
    # REDIS_PREFIX: str = Field(default="tangelo/")
    # REDIS_URL: str = Field(default="redis://127.0.0.1:6379")

    EMAIL_BACKEND: str = Field(default="django.core.mail.backends.console.EmailBackend")
    EMAIL_HOST_PASSWORD: str = Field(default="", help="SMTP email pass")

    FLICKR_API_KEY: str = Field(default="", help="API key issued by Flickr")
    FLICKR_API_SECRET: str = Field(default="", help="API secret issued by Flickr")
    FLICKR_USERNAME: str = Field(default="", help="Flickr username")

    # See table on this page for thumbnail size reference: https://www.flickr.com/services/api/misc.urls.html
    FLICKR_IMAGE_SIZE: str = Field(default="h", help="Image size for image detail view")
    FLICKR_THUMBNAIL_SIZE: str = Field(default="n", help="Thumnbail size for categories and images in grids")
    # Not currently using - Flickr's largest square is 150px, which we have to scale up and it looks bad.
    # Instead get size "n" and crop with CSS.
    FLICKR_CROPPED_THUMB_SIZE: str = Field(default="q", help="Cropped square thumnbail size for albums on homepage")

    LUMAPRINT_API_URL: str = Field(default="us.api.lumaprints.com", help="Override with sandbox URL locally")
    LUMAPRINT_API_KEY: str = Field(default="", help="")
    LUMAPRINT_API_SECRET: str = Field(default="", help="")


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
