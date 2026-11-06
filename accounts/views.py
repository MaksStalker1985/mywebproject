from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Max, Q, Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from catalog.models import Product
from payments.models import Order

from . import roles
from .avatars import AvatarForm, delete_avatar, save_avatar
from .forms import SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:cabinet")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Добро пожаловать, %(name)s! Регистрация прошла успешно.") % {"name": user.username})
        return redirect("accounts:cabinet")
    return render(request, "accounts/signup.html", {"form": form})


def _cabinet_stats(user):
    paid = user.orders.filter(status=Order.Status.PAID)
    return {
        "purchased": paid.values("product").distinct().count(),
        "spent": list(paid.values("currency").annotate(total=Sum("amount")).order_by("currency")),
        "pending": user.orders.filter(status=Order.Status.PENDING).count(),
    }


@login_required
def cabinet(request):
    """Личный кабинет: библиотека купленных (и доступных по роли) продуктов со скачиванием."""
    user = request.user
    library = (
        Product.objects.filter(orders__user=user, orders__status=Order.Status.PAID)
        .annotate(purchased_at=Max("orders__paid_at"))
        .order_by("-purchased_at")
    )
    role_products = Product.objects.none()
    if roles.has_free_access(user):
        # Платные продукты и тестовые сборки, которые группа получает без покупки
        role_products = (
            Product.objects.visible_to(user)
            .filter(Q(price__gt=0) | Q(is_published=False))
            .exclude(pk__in=library.values("pk"))
            .order_by("is_published", "title")
        )
    return render(request, "accounts/cabinet.html", {
        "tab": "library",
        "library": library,
        "role_products": role_products,
        "stats": _cabinet_stats(user),
    })


@login_required
def order_history(request):
    orders = request.user.orders.select_related("product")
    status = request.GET.get("status", "")
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    return render(request, "accounts/orders.html", {
        "tab": "orders",
        "page": Paginator(orders, 20).get_page(request.GET.get("page")),
        "status": status,
        "statuses": Order.Status.choices,
        "stats": _cabinet_stats(request.user),
    })


@login_required
def profile(request, avatar_form=None):
    user = request.user
    return render(
        request,
        "accounts/profile.html",
        {
            "tab": "profile",
            "topics": user.topics.select_related("category")[:10],
            "post_count": user.forum_posts.count(),
            "stats": _cabinet_stats(user),
            "avatar_form": avatar_form or AvatarForm(),
        },
    )


@login_required
@require_POST
def avatar_update(request):
    form = AvatarForm(request.POST, request.FILES)
    if not form.is_valid():
        return profile(request, avatar_form=form)
    save_avatar(request.user, form.cleaned_data["avatar"])
    messages.success(request, _("Аватар обновлён."))
    return redirect("accounts:profile")


@login_required
@require_POST
def avatar_remove(request):
    delete_avatar(request.user)
    messages.info(request, _("Аватар удалён."))
    return redirect("accounts:profile")
