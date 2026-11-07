import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts import roles
from catalog.models import Product, ProductImage
from forum.models import Category, CategoryAccess, Post, PostImage, Subforum, Topic

MEDIA = tempfile.mkdtemp(prefix="tv-img-")


def photo(name="shot.jpg", size=(2400, 1350), fmt="JPEG", exif=True):
    img = Image.new("RGB", size, (30, 120, 200))
    buf = io.BytesIO()
    kwargs = {}
    if exif and fmt == "JPEG":
        ex = Image.Exif()
        ex[0x010F] = "SecretCam"  # Make
        kwargs["exif"] = ex.tobytes()
    img.save(buf, fmt, **kwargs)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=MEDIA)
class ImageTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)


class ProductScreenshotTests(ImageTestCase):
    def setUp(self):
        self.admin = User.objects.create_user("boss", password="S3cure-pass!")
        roles.set_role(self.admin, roles.ADMINS)
        self.client.force_login(self.admin)
        self.product = Product.objects.create(slug="game", title="Game", short_description="s", description="d")

    def _post(self, files):
        data = {"kind": "game", "title": "Game", "slug": "game", "genre": "", "short_description": "s",
                "description": "d", "developer": "", "version": "1.0", "release_stage": "release",
                "platform": "windows", "price": "0", "changelog": "", "system_requirements": "",
                "is_published": "on", "screenshots": files}
        return self.client.post(reverse("dashboard:product_edit", args=[self.product.pk]), data)

    def test_admin_adds_screenshots_shown_in_gallery(self):
        self.assertRedirects(self._post([photo("a.jpg"), photo("b.png", fmt="PNG")]), reverse("dashboard:products"))
        shots = list(self.product.images.all())
        self.assertEqual(len(shots), 2)
        first = shots[0]
        self.assertEqual((first.width, first.height), (1920, 1080))  # уменьшено до 1920 px
        self.assertTrue(first.image.name.startswith("covers/screenshots/"))  # публичная папка
        with Image.open(first.image.path) as im:
            self.assertEqual(im.format, "WEBP")
            self.assertNotIn(0x010F, im.getexif())  # метаданные удалены
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, 'data-gallery="product"', count=2)
        self.assertContains(page, 'href="#screenshots"')

    def test_reorder_and_delete(self):
        self._post([photo("a.jpg"), photo("b.jpg")])
        a, b = self.product.images.all()
        self.client.post(reverse("dashboard:screenshot_action", args=[b.pk, "up"]))
        self.assertEqual(list(self.product.images.values_list("pk", flat=True)), [b.pk, a.pk])
        path = a.image.path
        self.client.post(reverse("dashboard:screenshot_action", args=[a.pk, "delete"]))
        self.assertFalse(ProductImage.objects.filter(pk=a.pk).exists())
        import os
        self.assertFalse(os.path.exists(path))  # файл тоже удалён

    def test_rejects_non_image(self):
        fake = SimpleUploadedFile("evil.jpg", b"<?php echo 1; ?>", content_type="image/jpeg")
        resp = self._post([fake])
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "не изображение")
        self.assertFalse(ProductImage.objects.exists())

    def test_non_admin_cannot_manage(self):
        self._post([photo()])
        shot = self.product.images.get()
        player = User.objects.create_user("p", password="S3cure-pass!")
        self.client.force_login(player)
        self.assertEqual(self.client.post(reverse("dashboard:screenshot_action", args=[shot.pk, "delete"])).status_code, 403)


class ForumPhotoTests(ImageTestCase):
    def setUp(self):
        self.cat = Category.objects.create(title="Игры", slug="games")
        self.sub = Subforum.objects.create(category=self.cat, title="Star Drift", slug="star-drift")
        self.user = User.objects.create_user("player", password="S3cure-pass!")
        self.client.force_login(self.user)

    def test_new_topic_with_photos_only(self):
        url = reverse("forum:subforum_topic_create", args=["games", "star-drift"])
        resp = self.client.post(url, {"title": "Мой корабль", "body": "", "images": [photo(), photo("2.png", fmt="PNG")]})
        topic = Topic.objects.get(title="Мой корабль")
        self.assertRedirects(resp, topic.get_absolute_url())
        first = topic.posts.get()
        self.assertEqual(first.images.count(), 2)
        self.assertTrue(first.images.first().image.name.startswith("forum/"))  # не в публичной папке
        page = self.client.get(topic.get_absolute_url())
        self.assertContains(page, f'data-gallery="post-{first.pk}"', count=2)

    def test_reply_needs_text_or_photo(self):
        topic = Topic.objects.create(subforum=self.sub, author=self.user, title="T")
        Post.objects.create(topic=topic, author=self.user, body="Q")
        resp = self.client.post(topic.get_absolute_url(), {"body": ""})
        self.assertContains(resp, "Напишите текст или прикрепите фото")
        self.client.post(topic.get_absolute_url(), {"body": "", "images": [photo()]})
        self.assertEqual(PostImage.objects.filter(post__topic=topic).count(), 1)

    def test_photo_access_follows_forum_permissions(self):
        topic = Topic.objects.create(subforum=self.sub, author=self.user, title="T")
        post = Post.objects.create(topic=topic, author=self.user, body="Q")
        self.client.post(topic.get_absolute_url(), {"body": "фото", "images": [photo()]})
        image = PostImage.objects.get()
        resp = self.client.get(image.get_absolute_url())
        self.assertEqual((resp.status_code, resp["Content-Type"]), (200, "image/webp"))
        resp.close()
        thumb = self.client.get(image.get_thumb_url())
        self.assertEqual(thumb.status_code, 200)
        thumb.close()
        # Гость не видит фото форума
        self.client.logout()
        self.assertEqual(self.client.get(image.get_absolute_url()).status_code, 302)
        # Группа без доступа к главной теме — тоже
        other = User.objects.create_user("other", password="S3cure-pass!")
        CategoryAccess.objects.create(category=self.cat, role=roles.get_role(other), level="none")
        self.client.force_login(other)
        self.assertEqual(self.client.get(image.get_absolute_url()).status_code, 404)
        # Удаление сообщения удаляет и файлы
        path = image.image.path
        post.topic.delete()
        import os
        self.assertFalse(os.path.exists(path))

    @override_settings(DOWNLOADS_ACCEL_PREFIX="/protected-media")
    def test_photo_served_by_nginx_in_production(self):
        topic = Topic.objects.create(subforum=self.sub, author=self.user, title="T")
        Post.objects.create(topic=topic, author=self.user, body="Q")
        self.client.post(topic.get_absolute_url(), {"body": "", "images": [photo()]})
        image = PostImage.objects.get()
        resp = self.client.get(image.get_absolute_url())
        self.assertEqual(resp["X-Accel-Redirect"], "/protected-media/" + image.image.name)

    def test_too_many_photos(self):
        topic = Topic.objects.create(subforum=self.sub, author=self.user, title="T")
        Post.objects.create(topic=topic, author=self.user, body="Q")
        resp = self.client.post(topic.get_absolute_url(), {"body": "x", "images": [photo(f"{i}.jpg", size=(50, 50)) for i in range(9)]})
        self.assertContains(resp, "не больше 8 фото")
