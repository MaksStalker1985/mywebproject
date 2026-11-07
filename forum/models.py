"""Форум: главная тема → подтема → публикация (обсуждение или вопрос с ответами) → сообщения."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

DEFAULT_SUBFORUM_SLUG = "general"


class Category(models.Model):
    """Главная тема форума. Доступ групп настраивается на этом уровне и действует на все её подтемы."""

    title = models.CharField(_("название"), max_length=100)
    slug = models.SlugField(_("адрес"), unique=True)
    description = models.CharField(_("описание"), max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(_("порядок"), default=0)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = _("главная тема")
        verbose_name_plural = _("главные темы")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:category", args=[self.slug])

    def default_subforum(self):
        """Первая подтема; если подтем нет — создаёт «Общее обсуждение»."""
        sub = self.subforums.order_by("order", "title").first()
        if sub is None:
            sub = Subforum.objects.create(category=self, title=_("Общее обсуждение"), slug=DEFAULT_SUBFORUM_SLUG)
        return sub


class Subforum(models.Model):
    """Подтема внутри главной темы; содержит публикации."""

    category = models.ForeignKey(
        Category, verbose_name=_("главная тема"), on_delete=models.CASCADE, related_name="subforums"
    )
    title = models.CharField(_("название"), max_length=100)
    slug = models.SlugField(_("адрес"))
    description = models.CharField(_("описание"), max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(_("порядок"), default=0)

    class Meta:
        ordering = ["category__order", "order", "title"]
        constraints = [models.UniqueConstraint(fields=["category", "slug"], name="unique_subforum_slug")]
        verbose_name = _("подтема")
        verbose_name_plural = _("подтемы")

    def __str__(self):
        return f"{self.category} → {self.title}"

    def get_absolute_url(self):
        return reverse("forum:subforum", args=[self.category.slug, self.slug])


class Topic(models.Model):
    """Публикация: обсуждение или вопрос, на который отвечают участники."""

    class Kind(models.TextChoices):
        DISCUSSION = "discussion", _("Обсуждение")
        QUESTION = "question", _("Вопрос")

    subforum = models.ForeignKey(
        Subforum, verbose_name=_("подтема"), on_delete=models.CASCADE, related_name="topics"
    )
    # Дублирует subforum.category: по главной теме проверяется доступ групп и считается статистика
    category = models.ForeignKey(
        Category, verbose_name=_("главная тема"), on_delete=models.CASCADE, related_name="topics", editable=False
    )
    kind = models.CharField(_("тип"), max_length=12, choices=Kind.choices, default=Kind.DISCUSSION)
    title = models.CharField(_("заголовок"), max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("автор"), on_delete=models.CASCADE, related_name="topics"
    )
    solution = models.ForeignKey(
        "Post", verbose_name=_("лучший ответ"), on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    is_pinned = models.BooleanField(_("закреплена"), default=False)
    is_locked = models.BooleanField(_("закрыта"), default=False)
    created_at = models.DateTimeField(_("создана"), auto_now_add=True)
    last_activity = models.DateTimeField(_("последняя активность"), auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-last_activity"]
        verbose_name = _("публикация")
        verbose_name_plural = _("публикации")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.subforum_id is None and self.category_id is not None:
            self.subforum = self.category.default_subforum()
        self.category_id = self.subforum.category_id
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("forum:topic", args=[self.pk])

    @property
    def is_question(self):
        return self.kind == self.Kind.QUESTION

    @property
    def is_solved(self):
        return self.is_question and self.solution_id is not None


class Post(models.Model):
    topic = models.ForeignKey(Topic, verbose_name=_("публикация"), on_delete=models.CASCADE, related_name="posts")
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
    """Уровень доступа группы к главной теме (и всем её подтемам). Нет записи — полный доступ."""

    class Level(models.TextChoices):
        NONE = "none", _("Нет доступа")
        READ = "read", _("Только чтение")
        WRITE = "write", _("Чтение и запись")

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="access_rules")
    role = models.ForeignKey("accounts.Role", on_delete=models.CASCADE, related_name="forum_access")
    level = models.CharField(_("доступ"), max_length=5, choices=Level.choices, default=Level.WRITE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["category", "role"], name="unique_category_role_access")]
        verbose_name = _("доступ к главной теме")
        verbose_name_plural = _("доступ к главным темам")

    def __str__(self):
        return f"{self.role} → {self.category}: {self.get_level_display()}"
