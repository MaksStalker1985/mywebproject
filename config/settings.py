"""Настройки проекта TechVault — портал распространения игр и ПО."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Все настройки для продакшена задаются переменными окружения (см. deploy/techvault.env.example).
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Задайте DJANGO_SECRET_KEY: без него сайт с DJANGO_DEBUG=0 не запускается.")
    SECRET_KEY = "django-insecure-dev-only-change-me-in-production"
SITE_DOMAINS = ["techvault.tech", "www.techvault.tech"]
# Переменная DJANGO_ALLOWED_HOSTS (задаёт install.sh) полностью заменяет это значение
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ",".join(["localhost", "127.0.0.1", *SITE_DOMAINS]))
# Полные адреса сайта для проверки CSRF за HTTPS-прокси, например https://example.com
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", ",".join(f"https://{d}" for d in SITE_DOMAINS))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "core",
    "catalog",
    "forum",
    "accounts",
    "payments",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.user_role",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# PostgreSQL, если задан POSTGRES_DB; иначе SQLite (для разработки)
if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ.get("POSTGRES_USER", ""),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", ""),  # пусто — локальный unix-сокет
            "PORT": os.environ.get("POSTGRES_PORT", ""),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Общий кеш (лимиты сброса пароля и т.п.) для нескольких процессов gunicorn
if os.environ.get("REDIS_URL"):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache",
                          "LOCATION": os.environ["REDIS_URL"]}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Многоязычность ---
LANGUAGE_CODE = "ru"
LANGUAGES = [
    ("ru", _("Русский")),
    ("en", _("English")),
    ("uk", _("Українська")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
TIME_ZONE = "Europe/Kyiv"
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))

MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
# Установочные файлы (media/downloads/) не публичны: их отдаёт nginx по внутреннему адресу после
# проверки покупки в Django (заголовок X-Accel-Redirect). Пусто — файл отдаёт сам Django.
DOWNLOADS_ACCEL_PREFIX = os.environ.get("DJANGO_DOWNLOADS_ACCEL_PREFIX", "")
# Загрузка больших установочных файлов через панель управления
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:cabinet"
LOGOUT_REDIRECT_URL = "core:home"

# Письма из формы обратной связи. В разработке выводятся в консоль;
# для продакшена задайте SMTP через переменные окружения.
EMAIL_DELIVERY_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "core.mail.EmailBackend"
)
# SMTP: DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend и параметры ниже
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
# 587 + STARTTLS (EMAIL_USE_TLS=1) или 465 + SSL (EMAIL_USE_SSL=1, как у Hostinger Mail)
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0") == "1"
EMAIL_USE_TLS = not EMAIL_USE_SSL and os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "TechVault <noreply@techvault.local>")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
# Адрес для ответов на письма сайта (алиас поддержки). EMAIL_HOST_USER — настоящий ящик для входа
# в SMTP; алиас (support@) в нём указывать нельзя.
EMAIL_REPLY_TO = [a.strip() for a in os.environ.get("EMAIL_REPLY_TO", "").split(",") if a.strip()]
EMAIL_BACKEND = "core.mail.ReplyToBackend" if EMAIL_REPLY_TO else EMAIL_DELIVERY_BACKEND

# Ссылка для сброса пароля действует 2 часа
PASSWORD_RESET_TIMEOUT = 2 * 60 * 60
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "support@techvault.tech")

# --- Платежи ---
# "demo" — имитация оплаты (только при DEBUG), "stripe" — Stripe Checkout, "paddle" — Paddle Billing.
PAYMENTS_PROVIDER = os.environ.get("PAYMENTS_PROVIDER", "demo" if DEBUG else "stripe")
PAYMENTS_CURRENCY = os.environ.get("PAYMENTS_CURRENCY", "UAH")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
# Paddle Billing: API-ключ (сервер), client-side token (Paddle.js), секрет webhook-уведомлений
PADDLE_API_KEY = os.environ.get("PADDLE_API_KEY", "")
PADDLE_CLIENT_TOKEN = os.environ.get("PADDLE_CLIENT_TOKEN", "")
PADDLE_WEBHOOK_SECRET = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
PADDLE_SANDBOX = os.environ.get("PADDLE_SANDBOX", "1" if DEBUG else "0") == "1"

# --- Безопасность в продакшене (за nginx с HTTPS) ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    # HSTS: начните с часа, после проверки HTTPS увеличьте до года (31536000)
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_HSTS_SUBDOMAINS", "0") == "1"
    SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_HSTS_PRELOAD", "0") == "1"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_HTTPONLY = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},  # в journald
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {"django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False}},
}
