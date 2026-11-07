"""Загрузка больших файлов по частям с возобновлением.

Браузер (static/js/chunked-upload.js) режет файл на части по UPLOAD_CHUNK_SIZE и отправляет их по
одной. Каждая часть — короткий запрос, поэтому нет упора в таймауты nginx/gunicorn и лимит размера
тела, а при обрыве связи загрузка продолжается с последнего принятого байта.

    POST   /manage/uploads/                 {"filename", "size"} → {"id", "chunk_size", "received"}
    GET    /manage/uploads/<id>/            → {"received", "size"}  (для продолжения)
    POST   /manage/uploads/<id>/chunk/      тело — байты части, заголовок X-Upload-Offset
    DELETE /manage/uploads/<id>/            отмена

Готовый файл привязывается к продукту при сохранении формы (поле upload_id в ProductForm).
"""
import json
import os
import shutil
from datetime import timedelta

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.utils.translation import gettext as _
from django.views import View

from catalog.models import Upload

from .views import StaffRequiredMixin

READ_BLOCK = 1024 * 1024
STALE_AFTER = timedelta(days=2)


def _error(message, status=400, **extra):
    return JsonResponse({"error": message, **extra}, status=status)


def _cleanup_stale():
    """Удаляет брошенные незавершённые загрузки (закрыли вкладку и не вернулись)."""
    for upload in Upload.objects.filter(updated_at__lt=timezone.now() - STALE_AFTER):
        upload.discard()


class UploadCreateView(StaffRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body or b"{}")
            size = int(data.get("size", -1))
        except (ValueError, TypeError):
            return _error(_("Некорректный запрос."))
        filename = get_valid_filename(os.path.basename(str(data.get("filename", ""))))[:200]
        if not filename or size <= 0:
            return _error(_("Некорректный запрос."))
        if size > settings.UPLOAD_MAX_SIZE:
            return _error(_("Файл слишком большой: максимум %(gb)s ГБ.") % {"gb": settings.UPLOAD_MAX_SIZE // 1024 ** 3},
                          status=413)
        _cleanup_stale()
        tmp_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(tmp_dir, exist_ok=True)
        # Файл копится во временной папке и потом переносится в downloads/ — нужен запас на диске
        if shutil.disk_usage(tmp_dir).free < size + 512 * 1024 * 1024:
            return _error(_("На сервере недостаточно свободного места для этого файла."), status=507)
        upload = Upload.objects.create(user=request.user, filename=filename, size=size)
        upload.temp_path.touch()
        return JsonResponse({"id": str(upload.pk), "chunk_size": settings.UPLOAD_CHUNK_SIZE, "received": 0},
                            status=201)


class UploadDetailView(StaffRequiredMixin, View):
    def get(self, request, pk):
        upload = get_object_or_404(Upload, pk=pk, user=request.user)
        received = upload.received
        # Сверяем с реальным размером временного файла (на случай сбоя между записью и сохранением)
        actual = upload.temp_path.stat().st_size if upload.temp_path.exists() else 0
        if actual != received:
            received = min(actual, received)
            Upload.objects.filter(pk=upload.pk).update(received=received)
        return JsonResponse({"id": str(upload.pk), "received": received, "size": upload.size,
                             "chunk_size": settings.UPLOAD_CHUNK_SIZE})

    def delete(self, request, pk):
        get_object_or_404(Upload, pk=pk, user=request.user).discard()
        return JsonResponse({"deleted": True})


class UploadChunkView(StaffRequiredMixin, View):
    def post(self, request, pk):
        try:
            offset = int(request.headers.get("X-Upload-Offset", ""))
            length = int(request.headers.get("Content-Length", ""))
        except ValueError:
            return _error(_("Некорректный запрос."))
        with transaction.atomic():
            upload = get_object_or_404(Upload.objects.select_for_update(), pk=pk, user=request.user)
            if offset != upload.received:
                # Часть уже принята или пропущена — браузер продолжит с указанного места
                return _error(_("Неверное смещение."), status=409, received=upload.received)
            if length <= 0 or length > settings.UPLOAD_CHUNK_SIZE or offset + length > upload.size:
                return _error(_("Некорректный размер части."))
            written = 0
            with open(upload.temp_path, "r+b") as out:
                out.seek(offset)
                out.truncate()
                while written < length:
                    block = request.read(min(READ_BLOCK, length - written))
                    if not block:
                        break
                    out.write(block)
                    written += len(block)
            if written != length:
                # Соединение оборвалось посреди части: отбрасываем её, браузер повторит
                with open(upload.temp_path, "r+b") as out:
                    out.truncate(offset)
                return _error(_("Часть получена не полностью."), status=400, received=offset)
            upload.received = offset + written
            upload.save(update_fields=["received", "updated_at"])
        return JsonResponse({"received": upload.received, "size": upload.size, "complete": upload.is_complete})


def attach_upload(upload, product):
    """Переносит собранный файл в downloads/ (на том же диске — мгновенно) и привязывает к продукту.
    Старый файл продукта удаляется, если им больше никто не пользуется."""
    name = default_storage.get_available_name(f"downloads/{upload.filename}")
    target = os.path.join(settings.MEDIA_ROOT, name)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    os.replace(upload.temp_path, target)
    os.chmod(target, 0o640)
    old = product.file.name if product.file else ""
    product.file.name = name
    product.save(update_fields=["file"])
    upload.delete()
    if old and old != name and not type(product).objects.filter(file=old).exists():
        default_storage.delete(old)
    return name
