"""Платёжные системы.

Провайдер выбирается настройкой PAYMENTS_PROVIDER:
- "stripe" — безналичная оплата картой (Visa/Mastercard, Apple Pay, Google Pay) через Stripe Checkout;
- "paddle" — оплата картой, PayPal, Apple/Google Pay через Paddle Billing (Merchant of Record);
- "demo"   — имитация оплаты для разработки, работает только при DEBUG=True.

Чтобы подключить другую систему (LiqPay, WayForPay, ЮKassa и т.п.), реализуйте класс
с теми же методами и добавьте его в PROVIDERS.
"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


class BaseProvider:
    name = ""

    def start_checkout(self, order, request):
        """Создаёт платёж и возвращает URL страницы оплаты."""
        raise NotImplementedError

    def sync(self, order):
        """Сверяет статус заказа с платёжной системой (на странице возврата)."""

    def refund(self, order, reason=""):
        """Возвращает деньги за оплаченный заказ через API платёжной системы."""
        raise NotImplementedError


class DemoProvider(BaseProvider):
    """Локальная страница «оплаты» без реальных денег — для разработки и демонстрации."""

    name = "demo"

    def __init__(self):
        if not settings.DEBUG:
            raise ImproperlyConfigured("Демо-оплата запрещена при DEBUG=False. Задайте PAYMENTS_PROVIDER=stripe.")

    def start_checkout(self, order, request):
        return reverse("payments:demo_checkout", args=[order.pk])

    def refund(self, order, reason=""):
        return f"demo-refund-{order.pk}"


class StripeProvider(BaseProvider):
    name = "stripe"

    def __init__(self):
        import stripe

        if not settings.STRIPE_SECRET_KEY:
            raise ImproperlyConfigured("Не задан STRIPE_SECRET_KEY")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stripe = stripe

    def start_checkout(self, order, request):
        result_url = request.build_absolute_uri(reverse("payments:result", args=[order.pk]))
        session = self.stripe.checkout.Session.create(
            mode="payment",
            client_reference_id=str(order.pk),
            metadata={"order_id": str(order.pk)},
            customer_email=order.user.email or None,
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": order.currency.lower(),
                        "unit_amount": order.amount_minor,
                        "product_data": {"name": f"{order.product.title} {order.product.version}"},
                    },
                }
            ],
            success_url=result_url,
            cancel_url=f"{result_url}?cancelled=1",
        )
        order.provider_payment_id = session.id
        order.save(update_fields=["provider_payment_id"])
        return session.url

    def sync(self, order):
        if order.status != order.Status.PENDING or not order.provider_payment_id:
            return
        session = self.stripe.checkout.Session.retrieve(order.provider_payment_id)
        self.apply_session(order, session.to_dict())

    @staticmethod
    def apply_session(order, session):
        """Применяет состояние Checkout Session (обычный dict) к заказу, проверяя сумму и валюту."""
        if session["payment_status"] != "paid":
            if session["status"] == "expired":
                order.mark(order.Status.CANCELLED)
            return
        if session["amount_total"] != order.amount_minor or session["currency"] != order.currency.lower():
            order.mark(order.Status.FAILED)
            return
        order.mark_paid(session.get("payment_intent") or session["id"])

    def parse_webhook(self, payload, signature):
        event = self.stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        return event.to_dict()

    def refund(self, order, reason=""):
        refund = self.stripe.Refund.create(payment_intent=order.provider_payment_id, metadata={"order_id": str(order.pk)})
        return refund.id


class PaddleProvider(BaseProvider):
    """Paddle Billing: транзакция создаётся на сервере, оплата — в оверлее Paddle.js на нашей странице.

    Paddle работает как Merchant of Record: сам считает и платит налоги (VAT/sales tax) с продаж.
    """

    name = "paddle"
    PAID_STATUSES = {"paid", "completed"}
    SIGNATURE_TOLERANCE = 300  # секунд

    def __init__(self):
        if not settings.PADDLE_API_KEY:
            raise ImproperlyConfigured("Не задан PADDLE_API_KEY")
        self.base_url = "https://sandbox-api.paddle.com" if settings.PADDLE_SANDBOX else "https://api.paddle.com"

    # События, на которые должен быть подписан адрес уведомлений (команда paddle setup-webhook)
    WEBHOOK_EVENTS = ["transaction.completed", "transaction.paid", "transaction.canceled",
                      "transaction.past_due", "adjustment.created", "adjustment.updated"]

    def _api(self, method, path, payload=None):
        req = urllib.request.Request(
            self.base_url + path,
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": f"Bearer {settings.PADDLE_API_KEY}", "Content-Type": "application/json",
                     "Paddle-Version": "1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.load(resp)["data"]
        except urllib.error.HTTPError as exc:
            # Paddle объясняет ошибку в теле ответа: {"error": {"code": ..., "detail": ...}}
            try:
                err = json.load(exc).get("error", {})
            except ValueError:
                err = {}
            raise PaddleError(exc.code, err.get("code", ""), err.get("detail", str(exc))) from exc

    def refund(self, order, reason=""):
        """Полный возврат: Paddle создаёт корректировку (adjustment), обычно одобряет её в течение
        нескольких минут и сообщает итог через webhook adjustment.updated."""
        adjustment = self._api("POST", "/adjustments", {
            "action": "refund",
            "type": "full",
            "transaction_id": order.provider_payment_id,
            "reason": reason or "Refund requested via TechVault",
        })
        return adjustment["id"]

    def start_checkout(self, order, request):
        name = f"{order.product.title} {order.product.version}"
        txn = self._api("POST", "/transactions", {
            "currency_code": order.currency,
            "custom_data": {"order_id": str(order.pk)},
            "items": [{
                "quantity": 1,
                "price": {
                    "description": name,
                    "unit_price": {"amount": str(order.amount_minor), "currency_code": order.currency},
                    "product": {"name": name, "tax_category": "standard"},
                },
            }],
        })
        order.provider_payment_id = txn["id"]
        order.save(update_fields=["provider_payment_id"])
        return reverse("payments:paddle_checkout", args=[order.pk])

    def sync(self, order):
        if order.status != order.Status.PENDING or not order.provider_payment_id:
            return
        self.apply_transaction(order, self._api("GET", f"/transactions/{order.provider_payment_id}"))

    @classmethod
    def apply_transaction(cls, order, txn):
        """Применяет состояние транзакции Paddle к заказу, сверяя ID, сумму и валюту."""
        if txn.get("id") != order.provider_payment_id:
            return
        status = txn.get("status")
        if status == "canceled":
            order.mark(order.Status.CANCELLED)
        elif status in cls.PAID_STATUSES:
            items = txn.get("items") or [{}]
            price = items[0].get("price", {}).get("unit_price", {})
            if price.get("amount") != str(order.amount_minor) or txn.get("currency_code") != order.currency:
                order.mark(order.Status.FAILED)
                return
            order.mark_paid(txn["id"])

    @staticmethod
    def apply_adjustment(order, adj):
        """Возвраты и чарджбэки из Paddle (в т.ч. оформленные в кабинете Paddle или банком покупателя).
        Частичный возврат доступ не закрывает."""
        action, status = adj.get("action"), adj.get("status")
        if action in {"refund", "chargeback"} and adj.get("type", "full") == "full":
            if status == "approved":
                order.mark_refunded(adj.get("id", ""))
            elif status == "rejected" and order.refund_id == adj.get("id"):
                order.restore_paid()
        elif action == "chargeback_reverse" and status == "approved":
            order.restore_paid()

    @classmethod
    def parse_webhook(cls, payload, signature_header):
        """Проверяет заголовок Paddle-Signature (ts=...;h1=...) и возвращает событие."""
        parts = dict(p.split("=", 1) for p in signature_header.split(";") if "=" in p)
        ts, received = parts.get("ts", ""), parts.get("h1", "")
        if not ts.isdigit() or abs(time.time() - int(ts)) > cls.SIGNATURE_TOLERANCE:
            raise ValueError("bad timestamp")
        expected = hmac.new(
            settings.PADDLE_WEBHOOK_SECRET.encode(), f"{ts}:".encode() + payload, hashlib.sha256
        ).hexdigest()
        if not settings.PADDLE_WEBHOOK_SECRET or not hmac.compare_digest(expected, received):
            raise ValueError("bad signature")
        return json.loads(payload)


class PaddleError(Exception):
    def __init__(self, status, code, detail):
        self.status, self.code, self.detail = status, code, detail
        super().__init__(f"Paddle API {status} {code}: {detail}")


def paddle_config_problems():
    """Список проблем настройки Paddle (пустой — всё в порядке). Используется в check и команде paddle."""
    problems = []
    key, token = settings.PADDLE_API_KEY, settings.PADDLE_CLIENT_TOKEN
    mode = "sandbox" if settings.PADDLE_SANDBOX else "live"
    if not key:
        problems.append("PADDLE_API_KEY не задан")
    elif "_sdbx_" in key and mode == "live":
        problems.append("PADDLE_API_KEY — ключ песочницы (sandbox), а PADDLE_SANDBOX=0")
    elif "_live_" in key and mode == "sandbox":
        problems.append("PADDLE_API_KEY — боевой ключ (live), а PADDLE_SANDBOX=1")
    if not token:
        problems.append("PADDLE_CLIENT_TOKEN не задан — окно оплаты не откроется")
    elif token.startswith("test_") and mode == "live":
        problems.append("PADDLE_CLIENT_TOKEN — токен песочницы (test_...), а PADDLE_SANDBOX=0")
    elif token.startswith("live_") and mode == "sandbox":
        problems.append("PADDLE_CLIENT_TOKEN — боевой токен (live_...), а PADDLE_SANDBOX=1")
    if not settings.PADDLE_WEBHOOK_SECRET:
        problems.append("PADDLE_WEBHOOK_SECRET не задан — сайт не узнает об оплатах и возвратах")
    return problems


PROVIDERS = {p.name: p for p in [DemoProvider, StripeProvider, PaddleProvider]}


def get_provider(name=None):
    name = name or settings.PAYMENTS_PROVIDER
    try:
        return PROVIDERS[name]()
    except KeyError:
        raise ImproperlyConfigured(f"Неизвестная платёжная система: {name}")
