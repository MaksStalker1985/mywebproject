import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Product
from core.models import ContactMessage
from forum.models import Category, Topic
from payments.models import Order

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class DashboardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.staff = User.objects.create_user("staff", "s@example.com", "S3cure-pass!", is_staff=True)
        self.user = User.objects.create_user("user", "u@example.com", "S3cure-pass!")

    def test_access_restricted_to_staff(self):
        url = reverse("dashboard:index")
        self.assertIn(reverse("accounts:login"), self.client.get(url).url)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_all_pages_render(self):
        self.client.force_login(self.staff)
        p = Product.objects.create(slug="x", title="X", short_description="s", description="d")
        c = Category.objects.create(slug="c", title="C")
        Topic.objects.create(category=c, author=self.user, title="T")
        ContactMessage.objects.create(name="n", email="e@example.com", message="m")
        Order.objects.create(user=self.user, product=p, amount=1, currency="UAH", provider="demo")
        for name, args in [("index", []), ("products", []), ("product_create", []), ("product_edit", [p.pk]),
                           ("product_delete", [p.pk]), ("categories", []), ("category_create", []),
                           ("category_edit", [c.pk]), ("topics", []), ("messages", []), ("orders", [])]:
            self.assertEqual(self.client.get(reverse(f"dashboard:{name}", args=args)).status_code, 200, name)

    def test_create_product_with_upload(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse("dashboard:product_create"), {
            "kind": "game", "title": "New Game", "slug": "", "short_description": "short", "description": "long",
            "version": "1.0", "release_stage": "release", "platform": "windows", "price": "250", "is_published": "on",
            "file": SimpleUploadedFile("setup.zip", b"zipdata"),
        })
        self.assertRedirects(resp, reverse("dashboard:products"))
        product = Product.objects.get(title="New Game")
        self.assertEqual((product.slug, product.price), ("new-game", Decimal("250")))
        self.assertTrue(product.file.name.endswith(".zip"))
        # Появился в публичном каталоге
        self.assertContains(self.client.get(reverse("catalog:games")), "New Game")

    def test_edit_and_delete_product(self):
        self.client.force_login(self.staff)
        p = Product.objects.create(slug="old", title="Old", short_description="s", description="d")
        data = {"kind": "software", "title": "Renamed", "slug": "old", "short_description": "s", "description": "d",
                "version": "2.0", "release_stage": "beta", "platform": "linux", "price": "0"}
        self.client.post(reverse("dashboard:product_edit", args=[p.pk]), data)
        p.refresh_from_db()
        self.assertEqual((p.title, p.version, p.is_published), ("Renamed", "2.0", False))
        self.client.post(reverse("dashboard:product_delete", args=[p.pk]))
        self.assertFalse(Product.objects.filter(pk=p.pk).exists())

    def test_product_with_orders_is_protected(self):
        self.client.force_login(self.staff)
        p = Product.objects.create(slug="sold", title="Sold", short_description="s", description="d", price=10)
        Order.objects.create(user=self.user, product=p, amount=10, currency="UAH", provider="demo", status="paid")
        resp = self.client.post(reverse("dashboard:product_delete", args=[p.pk]))
        self.assertRedirects(resp, reverse("dashboard:product_edit", args=[p.pk]))
        self.assertTrue(Product.objects.filter(pk=p.pk).exists())

    def test_toggles(self):
        self.client.force_login(self.staff)
        topic = Topic.objects.create(category=Category.objects.create(slug="c", title="C"), author=self.user, title="T")
        self.client.post(reverse("dashboard:topic_toggle", args=[topic.pk, "is_locked"]))
        msg = ContactMessage.objects.create(name="n", email="e@example.com", message="m")
        self.client.post(reverse("dashboard:message_toggle", args=[msg.pk]))
        topic.refresh_from_db()
        msg.refresh_from_db()
        self.assertTrue(topic.is_locked)
        self.assertTrue(msg.is_processed)

    def test_user_cannot_modify(self):
        self.client.force_login(self.user)
        p = Product.objects.create(slug="x", title="X", short_description="s", description="d")
        self.assertEqual(self.client.post(reverse("dashboard:product_delete", args=[p.pk])).status_code, 403)
        self.assertTrue(Product.objects.filter(pk=p.pk).exists())
