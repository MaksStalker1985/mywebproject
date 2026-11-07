"""Почтовый бэкенд для разработки: печатает письма в консоль в UTF-8.

Стандартный console.EmailBackend на Windows пишет в консоль в кодировке cp1252 и падает
на кириллице (UnicodeEncodeError), из-за чего письма сброса пароля и формы связи не «уходят».
"""
import sys

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend


class _Utf8Writer:
    """Пишет текст в байтовый буфер потока в UTF-8 (сам поток не закрывает)."""

    def __init__(self, stream):
        self._stream = stream
        self._buffer = getattr(stream, "buffer", None)

    def write(self, text):
        if self._buffer is None:
            self._stream.write(text)
        else:
            self._stream.flush()
            self._buffer.write(text.encode("utf-8", errors="replace"))

    def flush(self):
        (self._buffer or self._stream).flush()


class EmailBackend(ConsoleBackend):
    def __init__(self, *args, **kwargs):
        stream = kwargs.pop("stream", None) or sys.stdout
        super().__init__(*args, stream=_Utf8Writer(stream), **kwargs)


class ReplyToBackend(BaseEmailBackend):
    """Добавляет Reply-To (settings.EMAIL_REPLY_TO) письмам, у которых его нет, и передаёт их
    настоящему бэкенду (settings.EMAIL_DELIVERY_BACKEND)."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.inner = get_connection(settings.EMAIL_DELIVERY_BACKEND, fail_silently=fail_silently, **kwargs)

    def open(self):
        return self.inner.open()

    def close(self):
        return self.inner.close()

    def send_messages(self, email_messages):
        for message in email_messages:
            if not message.reply_to:
                message.reply_to = list(settings.EMAIL_REPLY_TO)
        return self.inner.send_messages(email_messages)
