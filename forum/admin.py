from django.contrib import admin

from .models import Category, Post, Subforum, Topic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "order"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(Subforum)
class SubforumAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "slug", "order"]
    list_filter = ["category"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["title"]}


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "subforum", "kind", "author", "is_pinned", "is_locked", "last_activity"]
    list_filter = ["category", "kind", "is_pinned", "is_locked"]
    raw_id_fields = ["solution"]
    list_editable = ["is_pinned", "is_locked"]
    search_fields = ["title"]
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["topic", "author", "created_at"]
    search_fields = ["body"]
