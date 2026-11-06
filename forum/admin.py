from django.contrib import admin

from .models import Category, Post, Topic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "order"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["title"]}


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "author", "is_pinned", "is_locked", "last_activity"]
    list_filter = ["category", "is_pinned", "is_locked"]
    list_editable = ["is_pinned", "is_locked"]
    search_fields = ["title"]
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["topic", "author", "created_at"]
    search_fields = ["body"]
