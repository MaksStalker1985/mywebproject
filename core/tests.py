import shutil
import tempfile

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models import Product
from core.models import ContactMessage
from forum.models import Category, Post, Topic

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class SiteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user("tester", "t@example.com", "S3cure-pass!")
        self.game = Product.objects.create(
            kind="game", slug="g1", title="Game One", short_description="s", description="d", is_featured=True
        )
        self.game.file.save("g1.zip", ContentFile(b"data"))
        self.app = Product.objects.create(kind="software", slug="a1", title="App One", short_description="s", description="d")
        self.cat = Category.objects.create(slug="general", title="General")

    # --- Страницы и языки ---
    def test_main_pages_in_all_languages(self):
        expected = {"ru": "Главная", "en": "Home", "uk": "Головна"}
        for lang, word in expected.items():
            with translation.override(lang):
                for name in ["core:home", "catalog:list", "catalog:games", "core:contact"]:
                    url = reverse(name)
                    self.assertTrue(url.startswith(f"/{lang}/"))
                    resp = self.client.get(url)
                    self.assertEqual(resp.status_code, 200, url)
                    self.assertContains(resp, word)

    def test_root_redirects_to_language(self):
        resp = self.client.get("/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertRedirects(resp, "/en/", fetch_redirect_response=False)

    def test_set_language_keeps_page(self):
        resp = self.client.post(reverse("set_language"), {"language": "uk", "next": "/ru/catalog/games/"})
        self.assertRedirects(resp, "/uk/catalog/games/", fetch_redirect_response=False)

    # --- Каталог ---
    def test_catalog_filters_by_kind(self):
        resp = self.client.get(reverse("catalog:software"))
        self.assertContains(resp, "App One")
        self.assertNotContains(resp, "Game One")

    def test_download_counts(self):
        resp = self.client.get(reverse("catalog:download", args=["g1"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(b"".join(resp.streaming_content), b"data")
        self.game.refresh_from_db()
        self.assertEqual(self.game.download_count, 1)
        self.assertEqual(self.client.get(reverse("catalog:download", args=["a1"])).status_code, 404)

    # --- Связь с производителем ---
    def test_contact_form_saves_and_mails(self):
        resp = self.client.post(
            reverse("core:contact"),
            {"name": "Ivan", "email": "i@example.com", "topic": "bug", "product": self.game.pk, "message": "Crash"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ContactMessage.objects.get().product, self.game)
        self.assertEqual(len(mail.outbox), 1)

    # --- Форум и учётные записи ---
    def test_forum_requires_login(self):
        topic = Topic.objects.create(category=self.cat, author=self.user, title="T")
        for url in [reverse("forum:index"), reverse("forum:category", args=["general"]), topic.get_absolute_url()]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse("accounts:login"), resp.url)

    def test_signup_logs_in_and_opens_forum(self):
        resp = self.client.post(
            reverse("accounts:signup"),
            {"username": "newbie", "email": "n@example.com", "password1": "Very-str0ng-pass", "password2": "Very-str0ng-pass"},
        )
        self.assertRedirects(resp, reverse("accounts:cabinet"))
        self.assertEqual(self.client.get(reverse("forum:index")).status_code, 200)
        from accounts.roles import PLAYERS, get_role
        self.assertEqual(get_role(User.objects.get(username="newbie")).key, PLAYERS)

    def test_create_topic_and_reply(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("forum:topic_create", args=["general"]), {"title": "Hello", "body": "First"})
        topic = Topic.objects.get(title="Hello")
        self.assertRedirects(resp, topic.get_absolute_url())
        self.client.post(topic.get_absolute_url(), {"body": "Second"})
        self.assertEqual(list(topic.posts.values_list("body", flat=True)), ["First", "Second"])

    def test_locked_topic_rejects_reply(self):
        self.client.force_login(self.user)
        topic = Topic.objects.create(category=self.cat, author=self.user, title="T", is_locked=True)
        self.assertEqual(self.client.post(topic.get_absolute_url(), {"body": "x"}).status_code, 403)

    def test_only_author_can_delete_post(self):
        topic = Topic.objects.create(category=self.cat, author=self.user, title="T")
        Post.objects.create(topic=topic, author=self.user, body="first")
        reply = Post.objects.create(topic=topic, author=self.user, body="reply")
        other = User.objects.create_user("other", password="x-Pass-123")
        self.client.force_login(other)
        self.assertEqual(self.client.post(reverse("forum:post_delete", args=[reply.pk])).status_code, 403)
        self.client.force_login(self.user)
        self.client.post(reverse("forum:post_delete", args=[reply.pk]))
        self.assertFalse(Post.objects.filter(pk=reply.pk).exists())
