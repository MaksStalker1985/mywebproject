from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "platform", "version", "download_count", "is_featured", "is_published"]
    list_filter = ["kind", "platform", "is_featured", "is_published"]
    list_editable = ["is_featured", "is_published"]
    search_fields = ["title", "short_description", "developer"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["download_count", "created_at", "updated_at"]
