"""Проверки настроек для развёртывания на сервере."""
import os
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from catalog.models import Product

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA, DOWNLOADS_ACCEL_PREFIX="/protected-media")
class AccelDownloadTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # счётчик скачиваний помнит посетителя сутки
        self.free = Product.objects.create(slug="free", title="Free", short_description="s", description="d")
        self.free.file.save("free game.zip", ContentFile(b"data"))
        self.paid = Product.objects.create(slug="paid", title="Paid", short_description="s", description="d",
                                           price=Decimal("10"))
        self.paid.file.save("paid.zip", ContentFile(b"secret"))

    def test_nginx_serves_file_after_django_check(self):
        resp = self.client.get(reverse("catalog:download", args=["free"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Accel-Redirect"], "/protected-media/" + self.free.file.name.replace(" ", "%20"))
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertEqual(resp.content, b"")  # содержимое отдаёт nginx
        self.free.refresh_from_db()
        self.assertEqual(self.free.download_count, 1)

    def test_paid_file_not_handed_to_nginx_without_purchase(self):
        self.client.force_login(User.objects.create_user("u", "u@example.com", "S3cure-pass!"))
        resp = self.client.get(reverse("catalog:download", args=["paid"]))
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("X-Accel-Redirect", resp)


class DevMediaTests(TestCase):
    def test_download_files_not_public_in_dev(self):
        downloads = Path(settings.MEDIA_ROOT) / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        probe = downloads / "_probe_test.zip"
        probe.write_bytes(b"x")
        try:
            self.assertEqual(self.client.get("/media/downloads/_probe_test.zip").status_code, 404)
        finally:
            probe.unlink()


class SeedGuardTests(TestCase):
    @override_settings(DEBUG=False)
    def test_seed_demo_refuses_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo")
        self.assertFalse(User.objects.filter(username="admin").exists())


class ProductionSettingsTests(SimpleTestCase):
    def _run(self, **env):
        full_env = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "POSTGRES_", "REDIS_"))}
        full_env.update(DJANGO_DEBUG="0", PYTHONIOENCODING="utf-8", **env)
        return subprocess.run([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
                              cwd=settings.BASE_DIR, env=full_env, capture_output=True, text=True, encoding="utf-8")

    def test_requires_secret_key(self):
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_deploy_check_is_clean(self):
        result = self._run(DJANGO_SECRET_KEY="x" * 60 + "-Production-Key-123",
                           DJANGO_ALLOWED_HOSTS="example.com", DJANGO_HSTS_SECONDS="31536000",
                           DJANGO_HSTS_SUBDOMAINS="1", DJANGO_HSTS_PRELOAD="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
