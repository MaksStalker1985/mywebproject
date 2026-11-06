"""Почтовый бэкенд для разработки: печатает письма в консоль в UTF-8.

Стандартный console.EmailBackend на Windows пишет в консоль в кодировке cp1252 и падает
на кириллице (UnicodeEncodeError), из-за чего письма сброса пароля и формы связи не «уходят».
"""
import sys

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
