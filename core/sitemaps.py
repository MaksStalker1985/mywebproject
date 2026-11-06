from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Product

from .models import Page


class StaticSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "weekly"

    def items(self):
        return ["core:home", "catalog:list", "catalog:games", "catalog:software", "core:contact"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(is_published=True).order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    i18n = True
    alternates = True
    changefreq = "monthly"
    priority = 0.3

    def items(self):
        return Page.objects.filter(is_published=True).order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"static": StaticSitemap, "products": ProductSitemap, "pages": PageSitemap}
