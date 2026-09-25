from .base import *

DEBUG = False

SECRET_KEY = os.environ["SECRET_KEY"]
if "POSTGRES_PASSWORD" in os.environ and not os.environ["POSTGRES_PASSWORD"]:
    raise RuntimeError("POSTGRES_PASSWORD must be set in environment")

ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "backend.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
        },
        "payments": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "payments.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 10,
        },
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "INFO"},
        "payments": {"handlers": ["payments"], "level": "INFO"},
    },
}

MPESA_ENV = os.environ.get("MPESA_ENV", "live")
