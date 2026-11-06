from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from .models import Product


def product_list(request, kind=None):
    products = Product.objects.filter(is_published=True)
    if kind:
        products = products.filter(kind=kind)

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(short_description__icontains=query) | Q(genre__icontains=query)
        )

    platform = request.GET.get("platform", "")
    if platform in Product.Platform.values:
        products = products.filter(platform=platform)

    sort = request.GET.get("sort", "new")
    products = products.order_by("-download_count" if sort == "popular" else "-created_at")

    page = Paginator(products, 9).get_page(request.GET.get("page"))
    return render(
        request,
        "catalog/list.html",
        {
            "page": page,
            "kind": kind,
            "query": query,
            "platform": platform,
            "sort": sort,
            "platforms": Product.Platform.choices,
            "kinds": Product.Kind,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not product.is_visible_to(request.user):
        raise Http404
    related = Product.objects.filter(is_published=True, kind=product.kind).exclude(pk=product.pk)[:3]
    return render(
        request,
        "catalog/detail.html",
        {
            "product": product,
            "related": related,
            "has_access": product.is_available_to(request.user),
            "purchased": product.is_purchased_by(request.user),
        },
    )


def product_download(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not product.is_visible_to(request.user):
        raise Http404
    if not product.file:
        raise Http404
    if not product.is_available_to(request.user):
        messages.info(request, _("Этот продукт платный. Купите его, чтобы скачать."))
        return redirect(product)
    try:
        handle = product.file.open("rb")
    except FileNotFoundError:
        raise Http404
    Product.objects.filter(pk=product.pk).update(download_count=F("download_count") + 1)
    return FileResponse(handle, as_attachment=True, filename=product.file.name.rsplit("/", 1)[-1])
