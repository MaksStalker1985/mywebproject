import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _


# Названия стандартных групп переводятся, пока администратор их не переименовал
SYSTEM_TITLES = {
    "admins": ("Администраторы", _("Администраторы")),
    "testers": ("Тестеры", _("Тестеры")),
    "players": ("Игроки", _("Игроки")),
}


class Role(models.Model):
    """Настройки группы пользователей. Сама группа — стандартная `auth.Group`; её имя служит ключом."""

    class Color(models.TextChoices):
        GREEN = "green", _("Зелёный")
        ORANGE = "orange", _("Оранжевый")
        RED = "red", _("Красный")
        BLUE = "blue", _("Синий")
        PURPLE = "purple", _("Фиолетовый")
        GRAY = "gray", _("Серый")

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    title = models.CharField(_("название"), max_length=60)
    description = models.CharField(_("описание"), max_length=255, blank=True)
    color = models.CharField(_("цвет значка"), max_length=10, choices=Color.choices, default=Color.GRAY)
    order = models.PositiveSmallIntegerField(_("порядок"), default=10,
                                             help_text=_("Если пользователь в нескольких группах, действует группа с меньшим числом."))

    can_access_dashboard = models.BooleanField(
        _("панель управления"), default=False,
        help_text=_("Управление каталогом, форумом, заказами, пользователями и группами; вход в Django admin."))
    can_moderate_forum = models.BooleanField(
        _("модерация форума"), default=False,
        help_text=_("Удаление чужих сообщений, ответы в закрытых темах, значок «Команда»."))
    free_access_paid = models.BooleanField(
        _("платные продукты бесплатно"), default=False,
        help_text=_("Скачивание платных игр и ПО без покупки."))
    can_see_test_builds = models.BooleanField(
        _("тестовые сборки"), default=False,
        help_text=_("Доступ к неопубликованным продуктам с отметкой «тестовая сборка»."))
    is_default = models.BooleanField(
        _("группа по умолчанию"), default=False,
        help_text=_("В эту группу попадают новые пользователи. Может быть только одна."))

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = _("группа пользователей")
        verbose_name_plural = _("группы пользователей")

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        original, translated = SYSTEM_TITLES.get(self.group.name, (None, None))
        return translated if self.title == original else self.title

    @property
    def key(self):
        return self.group.name

    @property
    def is_system(self):
        """Группу «Администраторы» нельзя удалить или лишить доступа к панели — иначе можно потерять управление сайтом."""
        from .roles import ADMINS

        return self.group.name == ADMINS

    @property
    def can_delete(self):
        return not self.is_system and not self.is_default


def avatar_upload_to(instance, filename):
    return f"avatars/{instance.user_id}-{uuid.uuid4().hex[:8]}.webp"


class Profile(models.Model):
    """Дополнительные данные пользователя: аватар для форума и личного кабинета."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(_("аватар"), upload_to=avatar_upload_to, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("профиль")
        verbose_name_plural = _("профили")

    def __str__(self):
        return str(self.user)
