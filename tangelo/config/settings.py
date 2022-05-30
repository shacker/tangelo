import os
import dj_database_url
from pathlib import Path

from .config import config  # Load secrets from settings.conf

config.load()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SECRET_KEY = config.SECRET_KEY
DEBUG = config.DEBUG
ALLOWED_HOSTS = config.ALLOWED_HOSTS


# Application definition

DATABASES = {"default": dj_database_url.parse(config.DATABASE_URL)}

# Static and media files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(PROJECT_ROOT, "static")]
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
MEDIA_ROOT = config.MEDIA_ROOT
MEDIA_URL = "/media/"

INSTALLED_APPS = [
    "django_light", # Disable admin dark mode
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "gallery",
    "markdownify.apps.MarkdownifyConfig",
    "adminsortable2",
    "crispy_forms",
    "jsoneditor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tangelo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [f"{str(PROJECT_ROOT)}/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "gallery.context_processors.nav_albums_list"
            ],
        },
    },
]

# See: http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

WSGI_APPLICATION = "tangelo.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

MANAGERS = ["shacker@birdhouse.org", ]

CACHES = {
    "default": {
        "BACKEND": config.CACHE_BACKEND,
        "LOCATION": "redis://127.0.0.1:6379",
        "KEY_PREFIX": "tangelo",
    }
}
# Cache lifetime - 1 year default (superuser use Clear Cache link on site)
CACHE_TTL = config.CACHE_TTL


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Los_Angeles"
USE_TZ = True

USE_I18N = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = config.EMAIL_BACKEND
DEFAULT_FROM_EMAIL = "shacker@birdhouse.org"

# Flickr stuff
FLICKR_API_KEY = config.FLICKR_API_KEY
FLICKR_API_SECRET = config.FLICKR_API_SECRET
FLICKR_USERNAME = config.FLICKR_USERNAME
FLICKR_THUMBNAIL_SIZE = config.FLICKR_THUMBNAIL_SIZE
FLICKR_IMAGE_SIZE = config.FLICKR_IMAGE_SIZE

# Defines how Markdownify bleaches/sanitizes, or allows HTML tags and attributes
# Allow myself (the onlyh administrator) to post any content type -
# other sites may want to lock this down.
MARKDOWNIFY = {
    "default": {
        "BLEACH": False
    },
}

# File logging on server only
if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/home/django/tangelo_debug.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'sub4.mail.dreamhost.com'
EMAIL_HOST_USER = 'gmailsender@birdhouse.org'
EMAIL_HOST_PASSWORD = config.EMAIL_HOST_PASSWORD

# JS and CSS for Admin JSON editor
# Check for upgrades at https://cdnjs.com/libraries/jsoneditor
JSON_EDITOR_JS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.7.4/jsoneditor.min.js"
JSON_EDITOR_CSS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/9.7.4/jsoneditor.min.css"
