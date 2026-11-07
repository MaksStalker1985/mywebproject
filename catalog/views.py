from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import content_disposition_header
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

    stage = request.GET.get("stage", "")
    if stage in Product.Stage.values:
        products = products.filter(release_stage=stage)

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
            "stage": stage,
            "stages": Product.Stage.choices,
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
    filename = product.file.name.rsplit("/", 1)[-1]
    if settings.DOWNLOADS_ACCEL_PREFIX:
        # Продакшен: права проверены здесь, сам файл отдаёт nginx из internal-локации
        if not product.file.storage.exists(product.file.name):
            raise Http404
        Product.objects.filter(pk=product.pk).update(download_count=F("download_count") + 1)
        response = HttpResponse(content_type="application/octet-stream")
        response["X-Accel-Redirect"] = settings.DOWNLOADS_ACCEL_PREFIX.rstrip("/") + "/" + quote(product.file.name)
        response["Content-Disposition"] = content_disposition_header(True, filename)
        return response
    try:
        handle = product.file.open("rb")
    except FileNotFoundError:
        raise Http404
    Product.objects.filter(pk=product.pk).update(download_count=F("download_count") + 1)
    return FileResponse(handle, as_attachment=True, filename=filename)
