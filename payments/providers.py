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


class DemoProvider(BaseProvider):
    """Локальная страница «оплаты» без реальных денег — для разработки и демонстрации."""

    name = "demo"

    def __init__(self):
        if not settings.DEBUG:
            raise ImproperlyConfigured("Демо-оплата запрещена при DEBUG=False. Задайте PAYMENTS_PROVIDER=stripe.")

    def start_checkout(self, order, request):
        return reverse("payments:demo_checkout", args=[order.pk])


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

    def _api(self, method, path, payload=None):
        req = urllib.request.Request(
            self.base_url + path,
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": f"Bearer {settings.PADDLE_API_KEY}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)["data"]

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


PROVIDERS = {p.name: p for p in [DemoProvider, StripeProvider, PaddleProvider]}


def get_provider(name=None):
    name = name or settings.PAYMENTS_PROVIDER
    try:
        return PROVIDERS[name]()
    except KeyError:
        raise ImproperlyConfigured(f"Неизвестная платёжная система: {name}")
