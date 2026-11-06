from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "topic", "product", "created_at", "is_processed"]
    list_filter = ["topic", "is_processed"]
    list_editable = ["is_processed"]
    search_fields = ["name", "email", "message"]
