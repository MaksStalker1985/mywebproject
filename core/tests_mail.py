from django.core import mail
from django.core.mail import EmailMessage
from django.test import TestCase, override_settings
from django.urls import reverse

LOCMEM = "django.core.mail.backends.locmem.EmailBackend"


@override_settings(EMAIL_BACKEND=LOCMEM, CONTACT_EMAIL="support@techvault.tech",
                   DEFAULT_FROM_EMAIL="TechVault <support@techvault.tech>")
class ContactMailTests(TestCase):
    def test_contact_form_mail_goes_to_alias_with_visitor_reply_to(self):
        resp = self.client.post(reverse("core:contact"), {
            "name": "Иван", "email": "ivan@example.com", "topic": "general", "message": "Привет"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["support@techvault.tech"])
        self.assertEqual(msg.from_email, "TechVault <support@techvault.tech>")
        self.assertEqual(msg.reply_to, ["ivan@example.com"])


@override_settings(EMAIL_BACKEND="core.mail.ReplyToBackend", EMAIL_DELIVERY_BACKEND=LOCMEM,
                   EMAIL_REPLY_TO=["support@techvault.tech"])
class ReplyToBackendTests(TestCase):
    def test_adds_reply_to_only_when_missing(self):
        EmailMessage("a", "b", "box@techvault.tech", ["u@example.com"]).send()
        EmailMessage("a", "b", "box@techvault.tech", ["u@example.com"], reply_to=["x@example.com"]).send()
        self.assertEqual([m.reply_to for m in mail.outbox], [["support@techvault.tech"], ["x@example.com"]])


class MailFailureTests(TestCase):
    @override_settings(EMAIL_BACKEND="core.tests_mail.BrokenBackend")
    def test_contact_form_logs_smtp_error_and_keeps_message(self):
        from core.models import ContactMessage
        with self.assertLogs("core.views", level="ERROR") as logs:
            resp = self.client.post(reverse("core:contact"), {
                "name": "Иван", "email": "ivan@example.com", "topic": "general", "message": "Привет"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertIn("SMTPAuthenticationError", "\n".join(logs.output))

    @override_settings(EMAIL_BACKEND="core.tests_mail.BrokenBackend", EMAIL_DELIVERY_BACKEND="smtp-test")
    def test_mailcheck_reports_auth_hint(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        with self.assertRaises(SystemExit):
            call_command("mailcheck", "u@example.com", stdout=out)
        self.assertIn("Подсказка: SMTP не принял логин/пароль", out.getvalue())


import smtplib  # noqa: E402

from django.core.mail.backends.base import BaseEmailBackend  # noqa: E402


class BrokenBackend(BaseEmailBackend):
    def send_messages(self, messages):
        raise smtplib.SMTPAuthenticationError(535, b"Incorrect authentication data")
