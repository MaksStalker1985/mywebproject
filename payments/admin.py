from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "user", "amount", "currency", "status", "provider", "created_at", "paid_at"]
    list_filter = ["status", "provider", "product"]
    search_fields = ["user__username", "user__email", "provider_payment_id"]
    readonly_fields = ["user", "product", "amount", "currency", "provider", "provider_payment_id", "created_at", "paid_at"]
    date_hierarchy = "created_at"
