import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ProductQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Опубликованные продукты; группам с правом «тестовые сборки» — ещё и они,
        группам с доступом к панели управления — всё."""
        from accounts import roles

        if roles.is_admin(user):
            return self
        if roles.can_see_test_builds(user):
            return self.filter(models.Q(is_published=True) | models.Q(for_testers=True))
        return self.filter(is_published=True)


class Product(models.Model):
    """Игра или программа, доступная для скачивания."""

    class Kind(models.TextChoices):
        GAME = "game", _("Игра")
        SOFTWARE = "software", _("Программа")

    class Platform(models.TextChoices):
        WINDOWS = "windows", "Windows"
        LINUX = "linux", "Linux"
        MACOS = "macos", "macOS"
        CROSS = "cross", _("Кроссплатформенная")

    class Stage(models.TextChoices):
        """Стадия выпуска текущей версии."""
        RELEASE = "release", _("Актуальная версия")
        BETA = "beta", _("Бета-тест")
        ALPHA = "alpha", _("Альфа-тест")

    kind = models.CharField(_("тип"), max_length=10, choices=Kind.choices, default=Kind.GAME)
    title = models.CharField(_("название"), max_length=150)
    slug = models.SlugField(_("адрес"), max_length=160, unique=True)
    genre = models.CharField(_("жанр / категория"), max_length=60, blank=True)
    short_description = models.CharField(_("кратко"), max_length=255)
    description = models.TextField(
        _("описание"),
        help_text=_("Пустая строка — новый абзац, «## » в начале строки — подзаголовок, «- » — пункт списка."),
    )
    developer = models.CharField(_("разработчик"), max_length=100, blank=True)
    version = models.CharField(_("версия"), max_length=30, default="1.0")
    release_stage = models.CharField(
        _("стадия"), max_length=10, choices=Stage.choices, default=Stage.RELEASE,
        help_text=_("Показывается в каталоге рядом с номером версии."),
    )
    changelog = models.TextField(
        _("что нового в версии"), blank=True,
        help_text=_("Список изменений текущей версии. Разметка как в описании."),
    )
    system_requirements = models.TextField(
        _("системные требования"), blank=True,
        help_text=_("Например: «- ОС: Windows 10 64-bit», «- Память: 8 ГБ». Разметка как в описании."),
    )
    platform = models.CharField(_("платформа"), max_length=10, choices=Platform.choices, default=Platform.WINDOWS)
    cover = models.ImageField(_("обложка"), upload_to="covers/", blank=True)
    file = models.FileField(_("файл"), upload_to="downloads/", blank=True)
    price = models.DecimalField(
        _("цена"), max_digits=10, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("0 — бесплатно. Валюта задаётся в настройках (PAYMENTS_CURRENCY)."),
    )
    download_count = models.PositiveIntegerField(_("скачиваний"), default=0)
    is_featured = models.BooleanField(_("на главной"), default=False)
    is_published = models.BooleanField(_("опубликовано"), default=True)
    for_testers = models.BooleanField(
        _("тестовая сборка"), default=False,
        help_text=_("Неопубликованный продукт будет доступен группам с правом «тестовые сборки»."),
    )
    created_at = models.DateTimeField(_("добавлено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлено"), auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("продукт")
        verbose_name_plural = _("продукты")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:detail", args=[self.slug])

    @property
    def is_free(self):
        return self.price <= 0

    @property
    def currency(self):
        return settings.PAYMENTS_CURRENCY

    def is_available_to(self, user):
        """Может ли пользователь скачать продукт: бесплатный, куплен, или у его группы есть право
        «платные продукты бесплатно»."""
        from accounts.roles import has_free_access

        if self.is_free:
            return True
        if not user.is_authenticated:
            return False
        return has_free_access(user) or self.is_purchased_by(user)

    def is_visible_to(self, user):
        """Страница продукта видна: опубликованный, доступный по роли, или уже купленный
        (купленное остаётся у покупателя, даже если продукт сняли с публикации)."""
        return (
            Product.objects.visible_to(user).filter(pk=self.pk).exists()
            or self.is_purchased_by(user)
        )

    def is_purchased_by(self, user):
        return user.is_authenticated and self.orders.filter(user=user, status="paid").exists()

    @property
    def is_test_build(self):
        return not self.is_published and self.for_testers

    @property
    def file_size(self):
        try:
            return self.file.size if self.file else None
        except FileNotFoundError:
            return None


class Upload(models.Model):
    """Загрузка большого файла по частям (панель управления): файл собирается в
    MEDIA_ROOT/uploads/<id>.part, после сохранения формы продукта переносится в downloads/."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads")
    filename = models.CharField(max_length=255)
    size = models.BigIntegerField()
    received = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("загрузка файла")
        verbose_name_plural = _("загрузки файлов")

    def __str__(self):
        return f"{self.filename} ({self.received}/{self.size})"

    @property
    def is_complete(self):
        return self.received == self.size

    @property
    def temp_path(self):
        return Path(settings.MEDIA_ROOT) / "uploads" / f"{self.pk}.part"

    def discard(self):
        self.temp_path.unlink(missing_ok=True)
        self.delete()
