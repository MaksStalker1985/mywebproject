"""Подключение и проверка Paddle.

    sudo techvault-manage paddle check
        режим (sandbox/live), ключи, доступ к API, адреса уведомлений (webhook)
    sudo techvault-manage paddle setup-webhook https://techvault.tech
        создаёт в Paddle адрес уведомлений для сайта и печатает секрет для PADDLE_WEBHOOK_SECRET
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from payments.providers import PaddleError, PaddleProvider, paddle_config_problems


class Command(BaseCommand):
    help = "Проверка и настройка подключения к Paddle"

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="action", required=True)
        sub.add_parser("check", help="проверить настройки и доступ к Paddle API")
        hook = sub.add_parser("setup-webhook", help="создать адрес уведомлений в Paddle")
        hook.add_argument("site_url", help="адрес сайта, например https://techvault.tech")

    def handle(self, *args, **options):
        if not settings.PADDLE_API_KEY:
            raise CommandError("PADDLE_API_KEY не задан в /etc/techvault/techvault.env")
        self.paddle = PaddleProvider()
        getattr(self, options["action"].replace("-", "_"))(options)

    def _webhook_path(self):
        return reverse("paddle_webhook")

    def check(self, options):
        mode = "SANDBOX (тестовые платежи)" if settings.PADDLE_SANDBOX else "LIVE (настоящие деньги)"
        self.stdout.write(f"  Режим                {mode}")
        self.stdout.write(f"  Платёжная система    {settings.PAYMENTS_PROVIDER}"
                          + ("" if settings.PAYMENTS_PROVIDER == "paddle" else "  ← укажите PAYMENTS_PROVIDER=paddle"))
        self.stdout.write(f"  Валюта               {settings.PAYMENTS_CURRENCY}")
        problems = paddle_config_problems()
        for p in problems:
            self.stdout.write(self.style.WARNING(f"  ! {p}"))

        try:
            destinations = self.paddle._api("GET", "/notification-settings")
        except PaddleError as exc:
            hint = " Проверьте ключ и режим PADDLE_SANDBOX." if exc.status in (401, 403) else ""
            raise CommandError(f"Paddle API не принял запрос: {exc.detail}.{hint}")
        except OSError as exc:
            raise CommandError(f"Нет связи с Paddle API: {exc}")
        self.stdout.write(self.style.SUCCESS("  ✓ API-ключ действует"))

        path = self._webhook_path()
        ours = [d for d in destinations if d.get("destination", "").rstrip("/").endswith(path.rstrip("/"))]
        if not ours:
            self.stdout.write(self.style.WARNING(
                f"  ! В Paddle нет адреса уведомлений …{path} — создайте его:\n"
                f"    sudo techvault-manage paddle setup-webhook https://ваш-домен"))
        for d in ours:
            events = {e.get("name") for e in d.get("subscribed_events", [])}
            missing = [e for e in PaddleProvider.WEBHOOK_EVENTS if e not in events]
            state = "активен" if d.get("active") else "ОТКЛЮЧЁН"
            self.stdout.write(f"  Уведомления → {d.get('destination')} ({state})")
            if missing:
                self.stdout.write(self.style.WARNING(f"  ! Не включены события: {', '.join(missing)}"))
        self.stdout.write(
            "\n  Ещё в кабинете Paddle:\n"
            "  • Checkout → Checkout settings → Default payment link: https://ваш-домен/payments/paddle/pay/\n"
            "  • Checkout → Website approval: добавьте домен сайта (для live-режима — обязательно)")
        if not problems and ours:
            self.stdout.write(self.style.SUCCESS("\n  Paddle подключён."))

    def setup_webhook(self, options):
        url = options["site_url"].rstrip("/") + self._webhook_path()
        if not url.startswith("https://"):
            raise CommandError("Адрес сайта должен начинаться с https:// — Paddle не шлёт уведомления по http.")
        try:
            existing = [d for d in self.paddle._api("GET", "/notification-settings") if d.get("destination") == url]
            if existing:
                raise CommandError(f"Адрес {url} уже есть в Paddle ({existing[0]['id']}). Секрет можно посмотреть "
                                   "в кабинете: Developer tools → Notifications → … → Edit destination.")
            dest = self.paddle._api("POST", "/notification-settings", {
                "description": "TechVault",
                "type": "url",
                "destination": url,
                "subscribed_events": PaddleProvider.WEBHOOK_EVENTS,
                "api_version": 1,
            })
        except PaddleError as exc:
            raise CommandError(f"Paddle API: {exc.detail}")
        self.stdout.write(self.style.SUCCESS(f"Адрес уведомлений создан: {url}"))
        self.stdout.write(
            "\nДобавьте секрет в /etc/techvault/techvault.env и перезапустите сайт:\n\n"
            f"  PADDLE_WEBHOOK_SECRET={dest.get('endpoint_secret_key', '')}\n\n"
            "  sudo systemctl restart django-site")
