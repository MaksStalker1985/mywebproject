from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    title = models.CharField(_("название"), max_length=100)
    slug = models.SlugField(_("адрес"), unique=True)
    description = models.CharField(_("описание"), max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(_("порядок"), default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = _("раздел")
        verbose_name_plural = _("разделы")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:category", args=[self.slug])


class Topic(models.Model):
    category = models.ForeignKey(Category, verbose_name=_("раздел"), on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(_("заголовок"), max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("автор"), on_delete=models.CASCADE, related_name="topics"
    )
    is_pinned = models.BooleanField(_("закреплена"), default=False)
    is_locked = models.BooleanField(_("закрыта"), default=False)
    created_at = models.DateTimeField(_("создана"), auto_now_add=True)
    last_activity = models.DateTimeField(_("последняя активность"), auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-last_activity"]
        verbose_name = _("тема")
        verbose_name_plural = _("темы")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:topic", args=[self.pk])


class Post(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_("тема"), on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("автор"), on_delete=models.CASCADE, related_name="forum_posts"
    )
    body = models.TextField(_("текст"))
    created_at = models.DateTimeField(_("создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("изменено"), auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("сообщение")
        verbose_name_plural = _("сообщения")

    def __str__(self):
        return f"{self.author} — {self.topic}"


class CategoryAccess(models.Model):
    """Уровень доступа группы к разделу форума. Нет записи — полный доступ (чтение и запись)."""

    class Level(models.TextChoices):
        NONE = "none", _("Нет доступа")
        READ = "read", _("Только чтение")
        WRITE = "write", _("Чтение и запись")

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="access_rules")
    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE, related_name="forum_access")
    level = models.CharField(_("доступ"), max_length=5, choices=Level.choices, default=Level.WRITE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["category", "role"], name="unique_category_role_access")]
        verbose_name = _("доступ к разделу")
        verbose_name_plural = _("доступ к разделам")

    def __str__(self):
        return f"{self.role} → {self.category}: {self.get_level_display()}"
