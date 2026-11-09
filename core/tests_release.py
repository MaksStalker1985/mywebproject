"""Готовность к релизу: юридические страницы, SEO-файлы, страницы ошибок, возвраты."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from accounts import roles
from catalog.models import Product
from payments.models import Order

from .models import Page
from .templatetags.markup import simple_markup


class LegalPagesTests(TestCase):
    def test_default_pages_exist_in_three_languages(self):
        for slug in ("terms", "privacy", "refunds"):
            page = Page.objects.get(slug=slug)
            self.assertTrue(page.body_en and page.body_uk)
            resp = self.client.get(reverse("core:page", args=[slug]))
            self.assertContains(resp, "support@techvault.tech")
        with translation.override("en"):
            self.assertContains(self.client.get("/en/p/terms/"), "Terms of Service")
        with translation.override("uk"):
            self.assertContains(self.client.get("/uk/p/privacy/"), "Політика конфіденційності")

    def test_footer_links_and_unpublished_hidden(self):
        home = self.client.get(reverse("core:home"))
        self.assertContains(home, reverse("core:page", args=["refunds"]))
        Page.objects.filter(slug="refunds").update(is_published=False)
        self.assertEqual(self.client.get(reverse("core:page", args=["refunds"])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("core:home")), reverse("core:page", args=["refunds"]))

    def test_markup_escapes_html(self):
        html = simple_markup("## Заголовок\nТекст <script>alert(1)</script>\n\n- пункт\n- support@techvault.tech")
        self.assertIn("<h2>Заголовок</h2>", html)
        self.assertNotIn("<script>", html)
        self.assertIn("<ul><li>пункт</li>", html)
        self.assertIn('href="mailto:support@techvault.tech"', html)

    def test_admin_edits_page(self):
        admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(admin, roles.ADMINS)
        self.client.force_login(admin)
        page = Page.objects.get(slug="terms")
        self.assertContains(self.client.get(reverse("dashboard:pages")), "Условия использования")
        data = {"slug": "terms", "order": 1, "title_ru": "Условия", "title_en": "", "title_uk": "",
                "body_ru": "Продавец: ФОП Тест", "body_en": "", "body_uk": "", "show_in_footer": "on",
                "is_published": "on"}
        self.assertRedirects(self.client.post(reverse("dashboard:page_edit", args=[page.pk]), data),
                             reverse("dashboard:pages"))
        with translation.override("en"):  # пустой перевод — показывается русский текст
            self.assertContains(self.client.get("/en/p/terms/"), "ФОП Тест")

    def test_signup_requires_terms(self):
        data = {"username": "newbie", "email": "n@example.com", "password1": "Very-str0ng-pass",
                "password2": "Very-str0ng-pass"}
        resp = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="newbie").exists())
        self.assertContains(self.client.get(reverse("accounts:signup")), reverse("core:page", args=["privacy"]))


class SeoAndErrorsTests(TestCase):
    def test_robots_sitemap_favicon(self):
        robots = self.client.get("/robots.txt")
        self.assertEqual(robots["Content-Type"], "text/plain")
        self.assertContains(robots, "Sitemap: http://testserver/sitemap.xml")
        Product.objects.create(slug="star", title="Star", short_description="s", description="d")
        sitemap = self.client.get("/sitemap.xml")
        self.assertContains(sitemap, "/ru/catalog/star/")
        self.assertContains(sitemap, "/en/p/terms/")
        self.assertEqual(self.client.get("/favicon.ico").status_code, 301)

    def test_meta_tags(self):
        Product.objects.create(slug="star", title="Star", short_description="Space sim", description="d")
        resp = self.client.get(reverse("catalog:detail", args=["star"]))
        self.assertContains(resp, '<meta name="description" content="Space sim">')
        self.assertContains(resp, 'rel="canonical"')

    @override_settings(DEBUG=False)
    def test_custom_404_and_500(self):
        resp = self.client.get("/ru/no-such-page/")
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "Страница не найдена", status_code=404)
        self.assertIn("TechVault", render_to_string("500.html"))


class RefundTests(TestCase):
    def test_admin_marks_refund_and_access_is_revoked(self):
        buyer = User.objects.create_user("buyer", "u@example.com", "S3cure-pass!")
        product = Product.objects.create(slug="paid", title="Paid", short_description="s", description="d",
                                         price=Decimal("5"))
        order = Order.objects.create(user=buyer, product=product, amount=5, currency="USD", provider="paddle",
                                     status=Order.Status.PAID)
        self.assertTrue(product.is_available_to(buyer))
        url = reverse("dashboard:order_refund", args=[order.pk])
        self.client.force_login(buyer)
        self.assertEqual(self.client.post(url).status_code, 403)
        admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(admin, roles.ADMINS)
        self.client.force_login(admin)
        from unittest import mock
        with mock.patch("payments.providers.PaddleProvider.refund", return_value="adj_1"),                 mock.patch("payments.providers.PaddleProvider.__init__", return_value=None):
            self.client.post(url)
        order.refresh_from_db()
        self.assertEqual((order.status, order.refund_id), (Order.Status.REFUNDED, "adj_1"))
        self.assertFalse(product.is_available_to(buyer))


class OwnerLegalDocumentsTests(TestCase):
    def test_owner_documents_in_three_languages(self):
        for lang, title, marker in [("en", "Privacy Policy", "Data Controller"),
                                    ("ru", "Политика конфиденциальности", "Контролёр данных"),
                                    ("uk", "Політика конфіденційності", "Контролер даних")]:
            page = self.client.get(f"/{lang}/p/privacy/")
            self.assertContains(page, f"<h1>{title}</h1>", html=False)
            self.assertContains(page, marker)
            self.assertContains(page, "office@techvault.tech")
            self.assertNotContains(page, "[Insert")
        self.assertContains(self.client.get("/uk/p/refunds/"), "refund@techvault.tech")
        self.assertContains(self.client.get("/en/p/terms/"), "Governing Law")

    def test_short_addresses_follow_visitor_language(self):
        self.assertRedirects(self.client.get("/refund-policy", HTTP_ACCEPT_LANGUAGE="uk"), "/uk/p/refunds/")
        self.assertRedirects(self.client.get("/privacy-policy/", HTTP_ACCEPT_LANGUAGE="en"), "/en/p/privacy/")
        self.assertRedirects(self.client.get("/terms-of-service", HTTP_ACCEPT_LANGUAGE="ru"), "/ru/p/terms/")
