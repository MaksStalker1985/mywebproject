from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactMessage(models.Model):
    """Обращение к производителю, отправленное через форму связи."""

    class Topic(models.TextChoices):
        GENERAL = "general", _("Общий вопрос")
        SUPPORT = "support", _("Техническая поддержка")
        BUG = "bug", _("Сообщение об ошибке")
        BUSINESS = "business", _("Сотрудничество")

    name = models.CharField(_("имя"), max_length=100)
    email = models.EmailField(_("e-mail"))
    topic = models.CharField(_("тема"), max_length=20, choices=Topic.choices, default=Topic.GENERAL)
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name=_("продукт"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    message = models.TextField(_("сообщение"))
    created_at = models.DateTimeField(_("создано"), auto_now_add=True)
    is_processed = models.BooleanField(_("обработано"), default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("обращение")
        verbose_name_plural = _("обращения")

    def __str__(self):
        return f"{self.name} <{self.email}>: {self.get_topic_display()}"


class Page(models.Model):
    """Информационная страница (условия, конфиденциальность, возвраты…) с текстом на трёх языках.

    Разметка текста: пустая строка — новый абзац, «## » в начале строки — подзаголовок,
    «- » — пункт списка. HTML не допускается.
    """

    slug = models.SlugField(_("адрес"), unique=True)
    title_ru = models.CharField(_("заголовок (RU)"), max_length=150)
    title_en = models.CharField(_("заголовок (EN)"), max_length=150, blank=True)
    title_uk = models.CharField(_("заголовок (UK)"), max_length=150, blank=True)
    body_ru = models.TextField(_("текст (RU)"))
    body_en = models.TextField(_("текст (EN)"), blank=True)
    body_uk = models.TextField(_("текст (UK)"), blank=True)
    show_in_footer = models.BooleanField(_("ссылка в подвале"), default=True)
    is_published = models.BooleanField(_("опубликовано"), default=True)
    order = models.PositiveSmallIntegerField(_("порядок"), default=0)
    updated_at = models.DateTimeField(_("обновлено"), auto_now=True)

    class Meta:
        ordering = ["order", "slug"]
        verbose_name = _("страница")
        verbose_name_plural = _("страницы")

    def __str__(self):
        return self.title_ru

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("core:page", args=[self.slug])

    def _localized(self, field):
        from django.utils.translation import get_language

        lang = (get_language() or "ru")[:2]
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_ru")

    @property
    def title(self):
        return self._localized("title")

    @property
    def body(self):
        return self._localized("body")
