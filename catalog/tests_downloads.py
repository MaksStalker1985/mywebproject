from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product


@override_settings(DOWNLOADS_ACCEL_PREFIX="/protected-media")
class DownloadCounterTests(TestCase):
    def setUp(self):
        cache.clear()
        self.product = Product.objects.create(slug="free", title="Free", short_description="s", description="d")
        self.product.file.save("free-setup.exe", ContentFile(b"data"))
        self.url = reverse("catalog:download", args=["free"])

    def tearDown(self):
        self.product.file.delete(save=False)

    def count(self):
        self.product.refresh_from_db()
        return self.product.download_count

    def test_repeat_and_resume_requests_count_once(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.get(self.url, HTTP_RANGE="bytes=1024-")          # докачка
        self.client.get(self.url, HTTP_RANGE="bytes=0-")             # повтор с начала в те же сутки
        self.client.get(self.url)
        self.client.head(self.url)
        self.assertEqual(self.count(), 1)

    def test_different_visitors_counted_separately(self):
        self.client.get(self.url, HTTP_X_REAL_IP="203.0.113.1")
        self.client.get(self.url, HTTP_X_REAL_IP="203.0.113.2")
        user = User.objects.create_user("u", password="S3cure-pass!")
        self.client.force_login(user)
        self.client.get(self.url, HTTP_X_REAL_IP="203.0.113.1")
        self.assertEqual(self.count(), 3)

    def test_resume_only_is_not_counted(self):
        self.client.get(self.url, HTTP_RANGE="bytes=500-999")
        self.assertEqual(self.count(), 0)
