import json
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import roles
from catalog.models import Product, Upload

MEDIA = tempfile.mkdtemp(prefix="tv-upl-")


@override_settings(MEDIA_ROOT=MEDIA, UPLOAD_CHUNK_SIZE=4)
class ChunkedUploadTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = User.objects.create_user("boss", password="S3cure-pass!")
        roles.set_role(self.admin, roles.ADMINS)
        self.client.force_login(self.admin)
        self.product = Product.objects.create(slug="game", title="Game", short_description="s", description="d")

    def _create(self, filename="setup.exe", size=10):
        r = self.client.post(reverse("dashboard:upload_create"), json.dumps({"filename": filename, "size": size}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["id"]

    def _chunk(self, upload_id, offset, data):
        return self.client.post(reverse("dashboard:upload_chunk", args=[upload_id]), data,
                                content_type="application/octet-stream", HTTP_X_UPLOAD_OFFSET=str(offset))

    def _upload(self, payload, filename="setup.exe"):
        upload_id = self._create(filename, len(payload))
        for offset in range(0, len(payload), 4):
            r = self._chunk(upload_id, offset, payload[offset:offset + 4])
            self.assertEqual(r.status_code, 200, r.content)
        return upload_id

    def _save_product(self, upload_id):
        data = {"kind": "game", "title": "Game", "slug": "game", "genre": "", "short_description": "s",
                "description": "d", "developer": "", "version": "1.0", "release_stage": "release",
                "platform": "windows", "price": "0", "changelog": "", "system_requirements": "",
                "is_published": "on", "upload_id": upload_id}
        return self.client.post(reverse("dashboard:product_edit", args=[self.product.pk]), data)

    def test_upload_in_chunks_and_attach_to_product(self):
        payload = b"0123456789"
        upload_id = self._upload(payload)
        upload = Upload.objects.get(pk=upload_id)
        self.assertTrue(upload.is_complete)
        temp = upload.temp_path
        self.assertRedirects(self._save_product(upload_id), reverse("dashboard:products"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.file.name, "downloads/setup.exe")
        self.assertEqual(Path(MEDIA, "downloads", "setup.exe").read_bytes(), payload)
        self.assertFalse(Upload.objects.exists())
        self.assertFalse(temp.exists())

    def test_replacing_file_removes_old_one(self):
        self._save_product(self._upload(b"old-file!!", "v1.zip"))
        self._save_product(self._upload(b"new-file!!", "v2.zip"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.file.name, "downloads/v2.zip")
        self.assertFalse(Path(MEDIA, "downloads", "v1.zip").exists())

    def test_resume_after_wrong_offset(self):
        upload_id = self._create(size=10)
        self.assertEqual(self._chunk(upload_id, 0, b"0123").status_code, 200)
        # Повтор той же части (ответ потерялся) — сервер сообщает, откуда продолжать
        r = self._chunk(upload_id, 0, b"0123")
        self.assertEqual((r.status_code, r.json()["received"]), (409, 4))
        status = self.client.get(reverse("dashboard:upload_detail", args=[upload_id])).json()
        self.assertEqual((status["received"], status["size"]), (4, 10))

    def test_incomplete_upload_rejected_by_form(self):
        upload_id = self._create(size=10)
        self._chunk(upload_id, 0, b"0123")
        r = self._save_product(upload_id)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Файл ещё загружается")

    def test_limits_and_validation(self):
        upload_id = self._create(size=6)
        self.assertEqual(self._chunk(upload_id, 0, b"012345").status_code, 400)  # больше части
        self._chunk(upload_id, 0, b"0123")
        self.assertEqual(self._chunk(upload_id, 4, b"4567").status_code, 400)  # за пределами файла
        with self.settings(UPLOAD_MAX_SIZE=100):
            r = self.client.post(reverse("dashboard:upload_create"), json.dumps({"filename": "a", "size": 101}),
                                 content_type="application/json")
            self.assertEqual(r.status_code, 413)
        r = self.client.post(reverse("dashboard:upload_create"), json.dumps({"filename": "../../etc/x", "size": 5}),
                             content_type="application/json")
        self.assertEqual(Upload.objects.get(pk=r.json()["id"]).filename, "x")

    def test_other_users_cannot_touch_upload(self):
        upload_id = self._create()
        other = User.objects.create_user("other-admin", password="S3cure-pass!")
        roles.set_role(other, roles.ADMINS)
        self.client.force_login(other)
        self.assertEqual(self._chunk(upload_id, 0, b"0123").status_code, 404)
        self.assertEqual(self._save_product(upload_id).status_code, 200)  # чужая загрузка не принимается
        player = User.objects.create_user("p", password="S3cure-pass!")
        self.client.force_login(player)
        self.assertEqual(self._chunk(upload_id, 0, b"0123").status_code, 403)

    def test_cancel_and_stale_cleanup(self):
        upload_id = self._create()
        path = Upload.objects.get(pk=upload_id).temp_path
        self.assertEqual(self.client.delete(reverse("dashboard:upload_detail", args=[upload_id])).status_code, 200)
        self.assertFalse(path.exists())
        stale_id = self._create()
        Upload.objects.filter(pk=stale_id).update(updated_at=timezone.now() - timedelta(days=3))
        self._create()  # новая загрузка заодно удаляет брошенные
        self.assertFalse(Upload.objects.filter(pk=stale_id).exists())

    def test_form_page_includes_uploader(self):
        r = self.client.get(reverse("dashboard:product_edit", args=[self.product.pk]))
        self.assertContains(r, "data-chunked-upload")
        self.assertContains(r, "chunked-upload.js")
        self.assertContains(r, 'id="upload-i18n"')
