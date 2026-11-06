"""Доступ групп пользователей к разделам форума.

Для каждой пары «раздел — группа» хранится уровень: нет доступа, только чтение, чтение и запись.
Если записи нет, доступ полный. Суперпользователь видит и пишет везде.
"""
from accounts import roles

from .models import CategoryAccess

NONE, READ, WRITE = CategoryAccess.Level.NONE, CategoryAccess.Level.READ, CategoryAccess.Level.WRITE


def _role_for(user):
    # Анонимным (главная страница) показываем то же, что группе по умолчанию
    return roles.get_role(user) if user is not None and user.is_authenticated else roles.default_role()


def _levels(user):
    """{category_id: level} для пользователя; кешируется на объекте пользователя."""
    cache_owner = user if user is not None and user.is_authenticated else None
    if cache_owner is not None and hasattr(cache_owner, "_forum_levels"):
        return cache_owner._forum_levels
    role = _role_for(user)
    levels = dict(CategoryAccess.objects.filter(role=role).values_list("category_id", "level")) if role else {}
    if cache_owner is not None:
        cache_owner._forum_levels = levels
    return levels


def _unrestricted(user):
    return user is not None and user.is_authenticated and user.is_superuser


def level(user, category):
    if _unrestricted(user):
        return WRITE
    return _levels(user).get(category.pk, WRITE)


def can_read(user, category):
    return level(user, category) != NONE


def can_write(user, category):
    return level(user, category) == WRITE


def visible_categories(user, queryset):
    if _unrestricted(user):
        return queryset
    hidden = [cat_id for cat_id, lvl in _levels(user).items() if lvl == NONE]
    return queryset.exclude(pk__in=hidden)


def visible_topics(user, queryset):
    if _unrestricted(user):
        return queryset
    hidden = [cat_id for cat_id, lvl in _levels(user).items() if lvl == NONE]
    return queryset.exclude(category_id__in=hidden)
