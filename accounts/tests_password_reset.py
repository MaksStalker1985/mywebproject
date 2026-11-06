import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .password_reset import RESET_LIMIT_PER_EMAIL, RESET_LIMIT_PER_IP


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("pilot", "Pilot@Example.com", "Old-pass-123!")

    def _request(self, email="pilot@example.com"):
        return self.client.post(reverse("accounts:password_reset"), {"email": email})

    def _link(self, message):
        return re.search(r"https?://[^\s]+/password/reset/[^\s]+/", message.body).group(0)

    def test_login_page_links_to_reset(self):
        self.assertContains(self.client.get(reverse("accounts:login")), reverse("accounts:password_reset"))

    def test_full_reset_flow(self):
        resp = self._request()  # регистр e-mail не важен
        self.assertRedirects(resp, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.user.email])
        self.assertIn("pilot", message.body)
        self.assertTrue(message.alternatives)  # HTML-версия письма

        link = self._link(message)
        resp = self.client.get(link)  # Django переносит токен в сессию и перенаправляет
        self.assertEqual(resp.status_code, 302)
        form_url = resp.url
        self.assertContains(self.client.get(form_url), "Новый пароль")
        resp = self.client.post(form_url, {"new_password1": "Brand-new-pass-77", "new_password2": "Brand-new-pass-77"})
        self.assertRedirects(resp, reverse("accounts:password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-new-pass-77"))
        # Уведомление о смене пароля
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("изменён", mail.outbox[1].subject)
        # Ссылка одноразовая
        self.client.logout()
        resp = self.client.get(link, follow=True)
        self.assertContains(resp, "Ссылка недействительна")

    def test_unknown_email_looks_the_same(self):
        resp = self._request("nobody@example.com")
        self.assertRedirects(resp, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_bad_token_rejected(self):
        self._request()
        link = self._link(mail.outbox[0])
        broken = re.sub(r"/([^/]+)/$", "/set-password-x/", link)
        resp = self.client.get(broken, follow=True)
        self.assertContains(resp, "Ссылка недействительна")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Old-pass-123!"))

    def test_weak_password_rejected(self):
        self._request()
        resp = self.client.get(self._link(mail.outbox[0]))
        resp = self.client.post(resp.url, {"new_password1": "12345", "new_password2": "12345"})
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Old-pass-123!"))

    def test_rate_limits(self):
        for _ in range(RESET_LIMIT_PER_EMAIL + 2):
            self._request()
        self.assertEqual(len(mail.outbox), RESET_LIMIT_PER_EMAIL)
        # Лимит с одного IP: дальше форма показывает ошибку
        cache.clear()
        for i in range(RESET_LIMIT_PER_IP):
            self._request(f"x{i}@example.com")
        resp = self._request("y@example.com")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Слишком много запросов")
