"""Загрузка аватаров: проверка файла, обрезка до квадрата, уменьшение и пересохранение в WebP.

Пересохранение через Pillow убирает метаданные (EXIF с геолокацией и т.п.) и любые «лишние» данные,
спрятанные в файле, — на сервер попадает только чистая картинка.
"""
import io

from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 3 * 1024 * 1024
MAX_SOURCE_SIDE = 6000
AVATAR_SIZE = 256
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


class AvatarForm(forms.Form):
    avatar = forms.FileField(
        label=_("Новый аватар"),
        help_text=_("JPG, PNG, WebP или GIF до 3 МБ. Картинка будет обрезана до квадрата 256×256."),
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp,image/gif"}),
    )

    def clean_avatar(self):
        upload = self.cleaned_data["avatar"]
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError(_("Файл больше 3 МБ."))
        try:
            return process_avatar(upload)
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
            raise forms.ValidationError(_("Не удалось прочитать изображение. Загрузите JPG, PNG, WebP или GIF."))


def process_avatar(upload):
    """Возвращает ContentFile с квадратным WebP-изображением AVATAR_SIZE×AVATAR_SIZE."""
    upload.seek(0)
    with Image.open(upload) as probe:
        if probe.format not in ALLOWED_FORMATS:
            raise ValueError("format")
        if max(probe.size) > MAX_SOURCE_SIDE:
            raise ValueError("too large")
        probe.verify()
    upload.seek(0)
    with Image.open(upload) as img:
        img.seek(0)  # для GIF — первый кадр
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA" if img.mode in {"RGBA", "LA", "P"} else "RGB")
        img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=86, method=4)
    return ContentFile(buf.getvalue(), name="avatar.webp")


def get_profile(user):
    from .models import Profile

    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def save_avatar(user, content):
    from .models import Profile

    profile, _created = Profile.objects.get_or_create(user=user)
    old = profile.avatar.name if profile.avatar else None
    profile.avatar.save("avatar.webp", content, save=True)
    if old:
        profile.avatar.storage.delete(old)
    return profile


def delete_avatar(user):
    profile = get_profile(user)
    if profile and profile.avatar:
        profile.avatar.delete(save=True)
