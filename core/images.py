"""Фотографии (скриншоты игр и программ, картинки на форуме).

Каждый файл проверяется Pillow, поворачивается по EXIF, уменьшается и пересохраняется в WebP:
метаданные (геолокация, модель камеры) и спрятанные в файле данные на сервер не попадают.
Сохраняются две версии: большая для просмотра и миниатюра для галереи.
"""
import io

from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
ACCEPT = "image/jpeg,image/png,image/webp,image/gif"
MAX_SOURCE_PIXELS = 50_000_000  # 50 Мп — защита от «бомб» с гигантским разрешением
FULL_SIDE = 1920
THUMB_SIDE = 480


class ProcessedImage:
    def __init__(self, full, thumb, width, height):
        self.full, self.thumb, self.width, self.height = full, thumb, width, height


def _webp(img, side, quality):
    copy = img.copy()
    copy.thumbnail((side, side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    copy.save(buf, "WEBP", quality=quality, method=4)
    return ContentFile(buf.getvalue()), copy.size


def process_image(upload):
    """Возвращает ProcessedImage или бросает ValueError, если файл не подходящая картинка."""
    upload.seek(0)
    try:
        with Image.open(upload) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise ValueError("format")
            if probe.size[0] * probe.size[1] > MAX_SOURCE_PIXELS:
                raise ValueError("too large")
            probe.verify()
        upload.seek(0)
        with Image.open(upload) as img:
            img.seek(0)  # GIF — первый кадр
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGBA" if img.mode in {"RGBA", "LA", "P"} else "RGB")
            full, size = _webp(img, FULL_SIDE, 86)
            thumb, _ = _webp(img, THUMB_SIDE, 80)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise ValueError("unreadable") from exc
    return ProcessedImage(full, thumb, *size)


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """Поле для выбора нескольких картинок сразу; проверяет и обрабатывает каждую."""

    def __init__(self, *args, max_files=10, max_bytes=10 * 1024 * 1024, **kwargs):
        self.max_files, self.max_bytes = max_files, max_bytes
        kwargs.setdefault("widget", MultipleImageInput(attrs={"accept": ACCEPT}))
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = [f for f in (data if isinstance(data, (list, tuple)) else [data]) if f]
        if not files:
            if self.required:
                raise forms.ValidationError(self.error_messages["required"], code="required")
            return []
        if len(files) > self.max_files:
            raise forms.ValidationError(_("Можно прикрепить не больше %(n)s фото за раз.") % {"n": self.max_files})
        result = []
        for f in files:
            if f.size > self.max_bytes:
                raise forms.ValidationError(_("«%(name)s» больше %(mb)s МБ.") % {
                    "name": f.name, "mb": self.max_bytes // (1024 * 1024)})
            try:
                result.append(process_image(f))
            except ValueError:
                raise forms.ValidationError(_("«%(name)s» — не изображение. Подходят JPG, PNG, WebP и GIF.") % {
                    "name": f.name})
        return result


def save_image(instance, processed):
    """Сохраняет обработанную картинку в поля image/thumb модели и саму модель."""
    instance.width, instance.height = processed.width, processed.height
    instance.image.save("image.webp", processed.full, save=False)
    instance.thumb.save("thumb.webp", processed.thumb, save=False)
    instance.save()
    return instance
