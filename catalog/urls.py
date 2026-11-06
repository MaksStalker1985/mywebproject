from django.urls import path

from . import views
from .models import Product

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("games/", views.product_list, {"kind": Product.Kind.GAME}, name="games"),
    path("software/", views.product_list, {"kind": Product.Kind.SOFTWARE}, name="software"),
    path("<slug:slug>/", views.product_detail, name="detail"),
    path("<slug:slug>/download/", views.product_download, name="download"),
]
