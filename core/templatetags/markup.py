"""Простая безопасная разметка для информационных страниц.

Пустая строка — новый абзац, «## » — подзаголовок, «### » — подзаголовок второго уровня, «- » — пункт списка. Весь текст экранируется,
ссылки и e-mail становятся кликабельными. HTML из текста не выполняется.
"""
import re

from django import template
from django.utils.html import format_html, urlize
from django.utils.safestring import mark_safe

register = template.Library()


def _inline(text):
    return urlize(text.strip(), nofollow=True, autoescape=True)


@register.filter
def simple_markup(text):
    out = []
    for block in re.split(r"\n\s*\n", (text or "").replace("\r\n", "\n").strip()):
        paragraph, items = [], []

        def flush_paragraph():
            if paragraph:
                out.append("<p>" + "<br>".join(paragraph) + "</p>")
                paragraph.clear()

        def flush_list():
            if items:
                out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
                items.clear()

        for line in block.split("\n"):
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("### "):
                flush_paragraph()
                flush_list()
                out.append(format_html("<h3>{}</h3>", line[4:].strip()))
            elif line.startswith("## "):
                flush_paragraph()
                flush_list()
                out.append(format_html("<h2>{}</h2>", line[3:].strip()))
            elif line.startswith("- "):
                flush_paragraph()
                items.append(_inline(line[2:]))
            else:
                flush_list()
                paragraph.append(_inline(line))
        flush_paragraph()
        flush_list()
    return mark_safe("\n".join(out))
