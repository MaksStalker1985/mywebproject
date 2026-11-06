from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("buy/<slug:slug>/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="orders"),
    path("orders/<int:pk>/", views.result, name="result"),
    path("orders/<int:pk>/demo/", views.demo_checkout, name="demo_checkout"),
    path("orders/<int:pk>/paddle/", views.paddle_checkout, name="paddle_checkout"),
]
