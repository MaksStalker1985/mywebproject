import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from catalog.models import Product

from .models import Order
from .providers import PaddleProvider, StripeProvider, get_provider

log = logging.getLogger(__name__)


@login_required
@require_POST
def checkout(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    if product.is_free or product.is_available_to(request.user):
        return redirect(product)

    provider = get_provider()
    order = Order.objects.create(
        user=request.user,
        product=product,
        amount=product.price,
        currency=product.currency,
        provider=provider.name,
    )
    try:
        return redirect(provider.start_checkout(order, request))
    except Exception:
        log.exception("Не удалось создать платёж для заказа %s", order.pk)
        order.mark(Order.Status.FAILED)
        messages.error(request, _("Не удалось перейти к оплате. Попробуйте позже или свяжитесь с нами."))
        return redirect(product)


def _own_order(request, pk):
    return get_object_or_404(Order.objects.select_related("product"), pk=pk, user=request.user)


@login_required
def result(request, pk):
    order = _own_order(request, pk)
    if order.status == Order.Status.PENDING:
        try:
            get_provider(order.provider).sync(order)
        except Exception:
            # Статус всё равно придёт через webhook
            log.exception("Не удалось проверить статус заказа %s", order.pk)
        if request.GET.get("cancelled"):
            order.mark(Order.Status.CANCELLED)
    return render(request, "payments/result.html", {"order": order})


@login_required
def demo_checkout(request, pk):
    order = _own_order(request, pk)
    if order.provider != "demo":
        raise Http404
    get_provider("demo")  # запрещено при DEBUG=False
    if order.status != Order.Status.PENDING:
        return redirect(order)
    if request.method == "POST":
        if request.POST.get("action") == "pay":
            order.mark_paid(f"demo-{order.pk}")
        else:
            order.mark(Order.Status.CANCELLED)
        return redirect(order)
    return render(request, "payments/demo_checkout.html", {"order": order})


@login_required
def paddle_checkout(request, pk):
    """Страница с оверлеем Paddle.js. Должна быть указана в Paddle как Default payment link."""
    order = _own_order(request, pk)
    if order.provider != "paddle" or not order.provider_payment_id:
        raise Http404
    if order.status != Order.Status.PENDING:
        return redirect(order)
    result_url = request.build_absolute_uri(order.get_absolute_url())
    return render(request, "payments/paddle_checkout.html", {
        "order": order,
        "paddle": {
            "token": settings.PADDLE_CLIENT_TOKEN,
            "sandbox": settings.PADDLE_SANDBOX,
            "transactionId": order.provider_payment_id,
            "email": request.user.email,
            "locale": get_language() if get_language() in {"en", "ru"} else None,
            "successUrl": result_url,
            "cancelUrl": f"{result_url}?cancelled=1",
        },
    })


@login_required
def paddle_payment_link(request):
    """Default payment link для Paddle: Paddle добавляет к нему ?_ptxn=<transaction id>."""
    order = get_object_or_404(
        Order, provider="paddle", provider_payment_id=request.GET.get("_ptxn", ""), user=request.user
    )
    return redirect("payments:paddle_checkout", order.pk)


@login_required
def order_list(request):
    """Старый адрес «Мои покупки» — теперь история покупок в личном кабинете."""
    return redirect("accounts:orders")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    provider = get_provider("stripe")
    try:
        event = provider.parse_webhook(request.body, request.headers.get("Stripe-Signature", ""))
    except Exception:
        return HttpResponseBadRequest("invalid signature")

    if event["type"] in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
        "checkout.session.expired",
    }:
        session = event["data"]["object"]
        order_id = (session.get("metadata") or {}).get("order_id")
        order = Order.objects.filter(pk=order_id, provider="stripe").first()
        if order:
            if event["type"] == "checkout.session.async_payment_failed":
                order.mark(Order.Status.FAILED)
            else:
                StripeProvider.apply_session(order, session)
    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def paddle_webhook(request):
    try:
        event = PaddleProvider.parse_webhook(request.body, request.headers.get("Paddle-Signature", ""))
    except ValueError:
        return HttpResponseBadRequest("invalid signature")

    if event.get("event_type", "").startswith("transaction."):
        txn = event.get("data") or {}
        order_id = (txn.get("custom_data") or {}).get("order_id")
        order = Order.objects.filter(pk=order_id, provider="paddle").first()
        if order:
            # Неудачная попытка (payment_failed) заказ не отменяет — покупатель может повторить оплату
            PaddleProvider.apply_transaction(order, txn)
    return HttpResponse(status=200)
