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
