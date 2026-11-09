from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """Покупка платного продукта. Доступ к скачиванию даёт заказ со статусом PAID."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает оплаты")
        PAID = "paid", _("Оплачен")
        CANCELLED = "cancelled", _("Отменён")
        FAILED = "failed", _("Ошибка оплаты")
        REFUNDED = "refunded", _("Возврат")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("покупатель"), on_delete=models.PROTECT, related_name="orders"
    )
    product = models.ForeignKey(
        "catalog.Product", verbose_name=_("продукт"), on_delete=models.PROTECT, related_name="orders"
    )
    # Цена фиксируется в момент заказа и не зависит от последующих изменений каталога
    amount = models.DecimalField(_("сумма"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("валюта"), max_length=3)
    status = models.CharField(_("статус"), max_length=10, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(_("платёжная система"), max_length=20)
    provider_payment_id = models.CharField(_("ID платежа"), max_length=255, blank=True, db_index=True)
    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    paid_at = models.DateTimeField(_("оплачен"), null=True, blank=True)
    refund_id = models.CharField(_("ID возврата"), max_length=255, blank=True)
    refunded_at = models.DateTimeField(_("возврат оформлен"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("заказ")
        verbose_name_plural = _("заказы")

    def __str__(self):
        return f"#{self.pk} {self.product} — {self.user} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse("payments:result", args=[self.pk])

    @property
    def amount_minor(self):
        """Сумма в минимальных единицах валюты (копейки/центы) для платёжных API."""
        return int(self.amount * 100)

    def mark_paid(self, payment_id=""):
        """Идемпотентно отмечает заказ оплаченным (вызывается и из webhook, и со страницы возврата)."""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.status == self.Status.PAID:
                return False
            order.status = self.Status.PAID
            order.paid_at = timezone.now()
            if payment_id:
                order.provider_payment_id = payment_id
            order.save(update_fields=["status", "paid_at", "provider_payment_id"])
        self.refresh_from_db()
        return True

    def mark_refunded(self, refund_id=""):
        """Возврат денег: доступ к скачиванию закрывается. Идемпотентно."""
        fields = {"status": self.Status.REFUNDED, "refunded_at": timezone.now()}
        if refund_id:
            fields["refund_id"] = refund_id
        changed = Order.objects.filter(pk=self.pk).exclude(status=self.Status.REFUNDED).update(**fields)
        self.refresh_from_db()
        return bool(changed)

    def restore_paid(self):
        """Возврат отклонён или чарджбэк отменён — доступ возвращается."""
        changed = Order.objects.filter(pk=self.pk, status=self.Status.REFUNDED).update(status=self.Status.PAID)
        self.refresh_from_db()
        return bool(changed)

    def mark(self, status):
        Order.objects.filter(pk=self.pk, status=self.Status.PENDING).update(status=status)
        self.refresh_from_db()
