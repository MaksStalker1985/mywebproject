import zlib

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def avatar(user, size=40, team=False):
    """Аватар пользователя: загруженная картинка или первая буква на цветном фоне (цвет зависит от логина)."""
    size = int(size)
    classes = "avatar avatar-team" if team else "avatar"
    name = getattr(user, "username", "") or "?"
    try:
        profile = user.profile
    except (ObjectDoesNotExist, AttributeError):  # профиль ещё не создан или анонимный пользователь
        profile = None
    if profile is not None and profile.avatar:
        return format_html(
            '<span class="{}" style="--size:{}px"><img src="{}" alt="{}" width="{}" height="{}" loading="lazy"></span>',
            classes, size, profile.avatar.url, name, size, size,
        )
    hue = zlib.crc32(name.encode("utf-8")) % 360
    return format_html('<span class="{}" style="--size:{}px;--hue:{}" aria-hidden="true">{}</span>',
                       classes, size, hue, name[:1].upper())
