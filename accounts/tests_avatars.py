import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from forum.models import Category, Post, Topic

from . import roles
from .models import Profile

MEDIA = tempfile.mkdtemp()


def image_file(name="a.png", size=(600, 400), fmt="PNG", color=(200, 30, 90)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(MEDIA_ROOT=MEDIA)
class AvatarTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user("pilot", "p@example.com", "S3cure-pass!")
        self.client.force_login(self.user)

    def test_upload_is_cropped_to_square_webp(self):
        resp = self.client.post(reverse("accounts:avatar_update"), {"avatar": image_file()})
        self.assertRedirects(resp, reverse("accounts:profile"))
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name.startswith("avatars/") and profile.avatar.name.endswith(".webp"))
        with Image.open(profile.avatar.path) as img:
            self.assertEqual((img.format, img.size), ("WEBP", (256, 256)))
        # Аватар виден на странице профиля и в шапке
        self.assertContains(self.client.get(reverse("accounts:profile")), profile.avatar.url)

    def test_replace_deletes_old_file_and_remove_works(self):
        self.client.post(reverse("accounts:avatar_update"), {"avatar": image_file()})
        old = Profile.objects.get(user=self.user).avatar
        old_path = old.path
        self.client.post(reverse("accounts:avatar_update"), {"avatar": image_file("b.jpg", fmt="JPEG")})
        profile = Profile.objects.get(user=self.user)
        self.assertNotEqual(profile.avatar.name, old.name)
        self.assertFalse(old.storage.exists(old.name), old_path)

        self.client.post(reverse("accounts:avatar_remove"))
        profile.refresh_from_db()
        self.assertFalse(profile.avatar)

    def test_rejects_non_images_and_big_files(self):
        fake = SimpleUploadedFile("evil.png", b"<?php echo 1; ?>", content_type="image/png")
        resp = self.client.post(reverse("accounts:avatar_update"), {"avatar": fake})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Не удалось прочитать изображение")
        big = SimpleUploadedFile("big.png", b"0" * (3 * 1024 * 1024 + 1), content_type="image/png")
        self.assertContains(self.client.post(reverse("accounts:avatar_update"), {"avatar": big}), "Файл больше 3 МБ")
        self.assertFalse(Profile.objects.filter(user=self.user).exclude(avatar="").exists())

    def test_forum_shows_avatars_and_letter_fallback(self):
        self.client.post(reverse("accounts:avatar_update"), {"avatar": image_file()})
        other = User.objects.create_user("zed", "z@example.com", "S3cure-pass!")
        cat = Category.objects.create(slug="c", title="C")
        topic = Topic.objects.create(category=cat, author=self.user, title="T")
        Post.objects.create(topic=topic, author=self.user, body="hi")
        Post.objects.create(topic=topic, author=other, body="yo")
        page = self.client.get(topic.get_absolute_url())
        self.assertContains(page, Profile.objects.get(user=self.user).avatar.url)
        self.assertContains(page, ">Z</span>")  # буква для пользователя без аватара

    def test_admin_can_remove_someones_avatar(self):
        self.client.post(reverse("accounts:avatar_update"), {"avatar": image_file()})
        url = reverse("dashboard:user_avatar_delete", args=[self.user.pk])
        self.assertEqual(self.client.post(url).status_code, 403)  # обычный игрок не может
        admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(admin, roles.ADMINS)
        self.client.force_login(admin)
        self.client.post(url)
        self.assertFalse(Profile.objects.get(user=self.user).avatar)
