"""Проверка почты: показывает настройки (без пароля) и отправляет тестовое письмо.

    sudo techvault-manage mailcheck                  # письмо на CONTACT_EMAIL
    sudo techvault-manage mailcheck you@example.com  # на указанный адрес
"""
import smtplib
import socket

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand

HINTS = [
    (smtplib.SMTPAuthenticationError,
     "SMTP не принял логин/пароль. В EMAIL_HOST_USER должен быть адрес настоящего ящика (не алиаса), "
     "в EMAIL_HOST_PASSWORD — пароль этого ящика (пароль с # или пробелами — в одинарных кавычках)."),
    (smtplib.SMTPSenderRefused,
     "Сервер не разрешает отправлять от DEFAULT_FROM_EMAIL. Укажите в DEFAULT_FROM_EMAIL сам ящик "
     "(EMAIL_HOST_USER) — ответы всё равно придут на EMAIL_REPLY_TO."),
    (smtplib.SMTPRecipientsRefused,
     "Сервер отклонил письмо. Если в тексте ошибки «Sender address rejected» — неверный отправитель: "
     "впишите DEFAULT_FROM_EMAIL=\"TechVault <support@ваш-домен>\". Иначе проверьте адрес получателя."),
    (smtplib.SMTPServerDisconnected,
     "Соединение оборвалось: проверьте пару порт/шифрование — 465 + EMAIL_USE_SSL=1 или 587 + EMAIL_USE_TLS=1."),
    ((socket.timeout, TimeoutError, ConnectionError, OSError),
     "Нет соединения с EMAIL_HOST:EMAIL_PORT. Проверьте адрес сервера и что исходящий порт не закрыт "
     "у хостинга/фаервола (на некоторых VPS исходящие 25/465/587 закрыты по умолчанию)."),
]


class Command(BaseCommand):
    help = "Показывает настройки почты и отправляет тестовое письмо"

    def add_arguments(self, parser):
        parser.add_argument("to", nargs="?", help="адрес получателя (по умолчанию CONTACT_EMAIL)")

    def handle(self, *args, **options):
        to = options["to"] or settings.CONTACT_EMAIL
        backend = getattr(settings, "EMAIL_DELIVERY_BACKEND", settings.EMAIL_BACKEND)
        rows = [
            ("Бэкенд", backend),
            ("Сервер", f"{settings.EMAIL_HOST}:{settings.EMAIL_PORT}"),
            ("Шифрование", "SSL" if settings.EMAIL_USE_SSL else ("STARTTLS" if settings.EMAIL_USE_TLS else "нет")),
            ("Логин (EMAIL_HOST_USER)", settings.EMAIL_HOST_USER or "— не задан —"),
            ("Пароль", "задан" if settings.EMAIL_HOST_PASSWORD else "— не задан —"),
            ("От кого (DEFAULT_FROM_EMAIL)", settings.DEFAULT_FROM_EMAIL),
            ("Ответы (EMAIL_REPLY_TO)", ", ".join(getattr(settings, "EMAIL_REPLY_TO", [])) or "—"),
            ("Форма связи (CONTACT_EMAIL)", settings.CONTACT_EMAIL),
            ("Получатель теста", to),
        ]
        for name, value in rows:
            self.stdout.write(f"  {name:<30} {value}")

        if "smtp" not in backend:
            self.stdout.write(self.style.ERROR(
                "\nПисьма не отправляются наружу: бэкенд не SMTP (письма печатаются в журнал). Добавьте в\n"
                "/etc/techvault/techvault.env строку DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n"
                "и перезапустите сайт: sudo systemctl restart django-site"))
            return

        self.stdout.write("\nОтправляю тестовое письмо…")
        try:
            with get_connection() as conn:
                EmailMessage(
                    subject="TechVault: проверка почты",
                    body="Если вы читаете это письмо — отправка почты с сайта работает.",
                    from_email=settings.DEFAULT_FROM_EMAIL, to=[to], connection=conn,
                ).send()
        except Exception as exc:  # показываем причину и подсказку
            self.stdout.write(self.style.ERROR(f"Ошибка: {type(exc).__name__}: {exc}"))
            for types, hint in HINTS:
                if isinstance(exc, types):
                    self.stdout.write(self.style.WARNING(f"Подсказка: {hint}"))
                    break
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f"Отправлено на {to}. Если письма нет — проверьте «Спам» и пересылку алиаса в hPanel."))
