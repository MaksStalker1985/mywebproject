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
