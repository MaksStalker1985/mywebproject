from django.contrib import admin

from forum.models import CategoryAccess

from .models import Role


class CategoryAccessInline(admin.TabularInline):
    model = CategoryAccess
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["title", "group", "can_access_dashboard", "can_moderate_forum", "free_access_paid",
                    "can_see_test_builds", "is_default", "order"]
    inlines = [CategoryAccessInline]
