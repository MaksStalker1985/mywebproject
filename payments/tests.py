import shutil
import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Product

from .models import Order

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA, DEBUG=True, PAYMENTS_PROVIDER="demo", PAYMENTS_CURRENCY="UAH")
class PaymentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user("buyer", "b@example.com", "S3cure-pass!")
        self.product = Product.objects.create(
            kind="game", slug="paid", title="Paid Game", short_description="s", description="d", price=Decimal("149.90")
        )
        self.product.file.save("paid.zip", ContentFile(b"secret"))
        self.download_url = reverse("catalog:download", args=["paid"])

    def test_paid_product_not_downloadable_without_purchase(self):
        self.assertRedirects(self.client.get(self.download_url), self.product.get_absolute_url())
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(self.download_url), self.product.get_absolute_url())

    def test_checkout_requires_login(self):
        resp = self.client.post(reverse("payments:checkout", args=["paid"]))
        self.assertIn(reverse("accounts:login"), resp.url)
        self.assertFalse(Order.objects.exists())

    def test_demo_purchase_flow(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("payments:checkout", args=["paid"]))
        order = Order.objects.get()
        self.assertEqual((order.amount, order.currency, order.status), (Decimal("149.90"), "UAH", "pending"))
        self.assertRedirects(resp, reverse("payments:demo_checkout", args=[order.pk]))

        self.client.post(reverse("payments:demo_checkout", args=[order.pk]), {"action": "pay"})
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")
        resp = self.client.get(self.download_url)
        self.assertEqual(b"".join(resp.streaming_content), b"secret")
        # Повторная покупка не нужна
        self.client.post(reverse("payments:checkout", args=["paid"]))
        self.assertEqual(Order.objects.count(), 1)

    def test_demo_cancel(self):
        self.client.force_login(self.user)
        self.client.post(reverse("payments:checkout", args=["paid"]))
        order = Order.objects.get()
        self.client.post(reverse("payments:demo_checkout", args=[order.pk]), {"action": "cancel"})
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertFalse(self.product.is_available_to(self.user))

    def test_cannot_view_foreign_order(self):
        order = Order.objects.create(user=self.user, product=self.product, amount=1, currency="UAH", provider="demo")
        self.client.force_login(User.objects.create_user("other", password="x-Pass-123"))
        self.assertEqual(self.client.get(reverse("payments:result", args=[order.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("payments:demo_checkout", args=[order.pk]), {"action": "pay"}).status_code, 404)

    @override_settings(DEBUG=False)
    def test_demo_provider_disabled_in_production(self):
        order = Order.objects.create(user=self.user, product=self.product, amount=1, currency="UAH", provider="demo")
        self.client.force_login(self.user)
        with self.assertRaises(Exception):
            self.client.post(reverse("payments:demo_checkout", args=[order.pk]), {"action": "pay"})
        order.refresh_from_db()
        self.assertEqual(order.status, "pending")


@override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_x", PAYMENTS_CURRENCY="UAH")
class StripeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", "b@example.com", "S3cure-pass!")
        self.product = Product.objects.create(
            kind="game", slug="paid", title="Paid", short_description="s", description="d", price=Decimal("100")
        )
        self.order = Order.objects.create(
            user=self.user, product=self.product, amount=Decimal("100"), currency="UAH", provider="stripe"
        )

    def _webhook(self, session, event_type="checkout.session.completed"):
        event = mock.Mock()
        event.to_dict.return_value = {"type": event_type, "data": {"object": session}}
        with mock.patch("stripe.Webhook.construct_event", return_value=event):
            return self.client.post(reverse("stripe_webhook"), b"{}", content_type="application/json",
                                    HTTP_STRIPE_SIGNATURE="t=1,v1=x")

    def _session(self, **kw):
        data = {"id": "cs_1", "payment_status": "paid", "status": "complete", "amount_total": 10000,
                "currency": "uah", "payment_intent": "pi_1", "metadata": {"order_id": str(self.order.pk)}}
        data.update(kw)
        return data

    def test_webhook_marks_paid(self):
        self.assertEqual(self._webhook(self._session()).status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual((self.order.status, self.order.provider_payment_id), ("paid", "pi_1"))
        self.assertTrue(self.product.is_available_to(self.user))

    def test_webhook_rejects_wrong_amount(self):
        self._webhook(self._session(amount_total=100))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "failed")

    def test_webhook_bad_signature(self):
        with mock.patch("stripe.Webhook.construct_event", side_effect=ValueError):
            resp = self.client.post(reverse("stripe_webhook"), b"{}", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_checkout_creates_stripe_session(self):
        session = mock.Mock(id="cs_new", url="https://checkout.stripe.com/c/pay/cs_new")
        self.client.force_login(User.objects.create_user("new", "n@example.com", "x-Pass-123"))
        with override_settings(PAYMENTS_PROVIDER="stripe"), \
                mock.patch("stripe.checkout.Session.create", return_value=session) as create:
            resp = self.client.post(reverse("payments:checkout", args=["paid"]))
        self.assertEqual(resp.url, session.url)
        params = create.call_args.kwargs
        self.assertEqual(params["line_items"][0]["price_data"]["unit_amount"], 10000)
        self.assertEqual(Order.objects.latest("pk").provider_payment_id, "cs_new")


@override_settings(PADDLE_API_KEY="pdl_test", PADDLE_CLIENT_TOKEN="test_tok", PADDLE_WEBHOOK_SECRET="pdl_ntfset_x",
                   PADDLE_SANDBOX=True, PAYMENTS_CURRENCY="USD")
class PaddleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", "b@example.com", "S3cure-pass!")
        self.product = Product.objects.create(
            kind="game", slug="paid", title="Paid", short_description="s", description="d", price=Decimal("19.99")
        )
        self.order = Order.objects.create(user=self.user, product=self.product, amount=Decimal("19.99"),
                                          currency="USD", provider="paddle", provider_payment_id="txn_1")

    def _txn(self, **kw):
        data = {"id": "txn_1", "status": "completed", "currency_code": "USD",
                "custom_data": {"order_id": str(self.order.pk)},
                "items": [{"price": {"unit_price": {"amount": "1999", "currency_code": "USD"}}}]}
        data.update(kw)
        return data

    def _post(self, body, ts=None, secret="pdl_ntfset_x"):
        import hashlib
        import hmac
        import json
        import time

        raw = json.dumps(body).encode()
        ts = str(int(ts if ts is not None else time.time()))
        h1 = hmac.new(secret.encode(), f"{ts}:".encode() + raw, hashlib.sha256).hexdigest()
        return self.client.post(reverse("paddle_webhook"), raw, content_type="application/json",
                                HTTP_PADDLE_SIGNATURE=f"ts={ts};h1={h1}")

    def test_webhook_marks_paid(self):
        self.assertEqual(self._post({"event_type": "transaction.completed", "data": self._txn()}).status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_webhook_rejects_bad_signature_and_old_timestamp(self):
        body = {"event_type": "transaction.completed", "data": self._txn()}
        self.assertEqual(self._post(body, secret="wrong").status_code, 400)
        self.assertEqual(self._post(body, ts=1).status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_webhook_checks_amount_and_transaction(self):
        self._post({"event_type": "transaction.completed", "data": self._txn(id="txn_other")})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self._post({"event_type": "transaction.completed", "data": self._txn(
            items=[{"price": {"unit_price": {"amount": "1", "currency_code": "USD"}}}])})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "failed")

    def test_checkout_creates_transaction_and_renders_paddle_js(self):
        buyer = User.objects.create_user("new", "n@example.com", "x-Pass-123")
        self.client.force_login(buyer)
        with override_settings(PAYMENTS_PROVIDER="paddle"), \
                mock.patch("payments.providers.PaddleProvider._api", return_value={"id": "txn_new"}) as api:
            resp = self.client.post(reverse("payments:checkout", args=["paid"]))
        order = Order.objects.get(provider_payment_id="txn_new")
        self.assertRedirects(resp, reverse("payments:paddle_checkout", args=[order.pk]))
        method, path, payload = api.call_args.args
        self.assertEqual((method, path), ("POST", "/transactions"))
        self.assertEqual(payload["items"][0]["price"]["unit_price"], {"amount": "1999", "currency_code": "USD"})
        page = self.client.get(resp.url)
        self.assertContains(page, "cdn.paddle.com/paddle/v2/paddle.js")
        self.assertContains(page, "txn_new")
        # Default payment link от Paddle ведёт на ту же страницу
        link = self.client.get(reverse("paddle_payment_link") + "?_ptxn=txn_new")
        self.assertRedirects(link, reverse("payments:paddle_checkout", args=[order.pk]))

    def test_return_page_syncs_status(self):
        self.client.force_login(self.user)
        with mock.patch("payments.providers.PaddleProvider._api", return_value=self._txn(status="paid")):
            self.client.get(reverse("payments:result", args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    # --- Возвраты и чарджбэки ---
    def _paid(self):
        self.order.mark_paid("txn_1")
        return self.order

    def _admin(self):
        from accounts import roles
        admin = User.objects.create_user("boss", "boss@example.com", "S3cure-pass!")
        roles.set_role(admin, roles.ADMINS)
        self.client.force_login(admin)

    def test_dashboard_refund_goes_to_paddle(self):
        self._paid()
        self._admin()
        with mock.patch("payments.providers.PaddleProvider._api", return_value={"id": "adj_1"}) as api:
            self.client.post(reverse("dashboard:order_refund", args=[self.order.pk]))
        method, path, payload = api.call_args.args
        self.assertEqual((method, path), ("POST", "/adjustments"))
        self.assertEqual((payload["action"], payload["type"], payload["transaction_id"]), ("refund", "full", "txn_1"))
        self.order.refresh_from_db()
        self.assertEqual((self.order.status, self.order.refund_id), ("refunded", "adj_1"))
        self.assertFalse(self.product.is_available_to(self.user))

    def test_dashboard_refund_error_keeps_order_paid(self):
        from payments.providers import PaddleError
        self._paid()
        self._admin()
        err = PaddleError(400, "transaction_not_refundable", "Transaction cannot be refunded")
        with mock.patch("payments.providers.PaddleProvider._api", side_effect=err):
            resp = self.client.post(reverse("dashboard:order_refund", args=[self.order.pk]), follow=True)
        self.assertContains(resp, "Transaction cannot be refunded")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def _adj(self, **kw):
        data = {"id": "adj_9", "action": "refund", "type": "full", "status": "approved", "transaction_id": "txn_1"}
        data.update(kw)
        return {"event_type": "adjustment.updated", "data": data}

    def test_refund_made_in_paddle_closes_access(self):
        self._paid()
        self._post(self._adj(status="pending_approval"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self._post(self._adj())
        self.order.refresh_from_db()
        self.assertEqual((self.order.status, self.order.refund_id), ("refunded", "adj_9"))

    def test_partial_refund_keeps_access_and_chargeback_flow(self):
        self._paid()
        self._post(self._adj(type="partial"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self._post(self._adj(id="adj_cb", action="chargeback"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "refunded")
        self._post(self._adj(id="adj_cbr", action="chargeback_reverse"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_rejected_refund_restores_access(self):
        self._paid()
        self.order.mark_refunded("adj_9")
        self._post(self._adj(status="rejected"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_config_problems(self):
        from payments.providers import paddle_config_problems
        with override_settings(PADDLE_API_KEY="pdl_live_apikey_x", PADDLE_CLIENT_TOKEN="test_x",
                               PADDLE_WEBHOOK_SECRET="", PADDLE_SANDBOX=True):
            problems = " ".join(paddle_config_problems())
        self.assertIn("боевой ключ", problems)
        self.assertIn("PADDLE_WEBHOOK_SECRET", problems)
        with override_settings(PADDLE_API_KEY="pdl_sdbx_apikey_x", PADDLE_CLIENT_TOKEN="test_x", PADDLE_SANDBOX=True):
            self.assertEqual(paddle_config_problems(), [])

    def test_paddle_command(self):
        from io import StringIO
        from django.core.management import call_command
        dest = {"id": "ntfset_1", "destination": "https://techvault.tech/payments/webhook/paddle/", "active": True,
                "subscribed_events": [{"name": "transaction.completed"}]}
        out = StringIO()
        with mock.patch("payments.providers.PaddleProvider._api", return_value=[dest]):
            call_command("paddle", "check", stdout=out)
        self.assertIn("API-ключ действует", out.getvalue())
        self.assertIn("adjustment.updated", out.getvalue())  # не включённое событие
        out = StringIO()
        with mock.patch("payments.providers.PaddleProvider._api",
                        side_effect=[[], {"id": "ntfset_2", "endpoint_secret_key": "pdl_ntfset_secret"}]) as api:
            call_command("paddle", "setup-webhook", "https://shop.example", stdout=out)
        payload = api.call_args.args[2]
        self.assertEqual(payload["destination"], "https://shop.example/payments/webhook/paddle/")
        self.assertIn("adjustment.updated", payload["subscribed_events"])
        self.assertIn("PADDLE_WEBHOOK_SECRET=pdl_ntfset_secret", out.getvalue())
