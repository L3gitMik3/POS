from .base import *

# SQLite has one database and no PostgreSQL schemas. Treat tenant apps as
# shared for local development so their tables are created in dev.sqlite3.
SHARED_APPS = list(dict.fromkeys(SHARED_APPS + TENANT_APPS))
INSTALLED_APPS = SHARED_APPS

DATABASES = {
    "default": {
        "ENGINE": "core.sqlite_backend",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

MPESA_ENV = "sandbox"
FAKE_DARAJA = True
