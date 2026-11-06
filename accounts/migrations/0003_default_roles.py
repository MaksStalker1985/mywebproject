"""Настройки для трёх стандартных групп: прежние права администраторов, тестеров и игроков."""
from django.db import migrations

DEFAULTS = {
    "admins": dict(title="Администраторы", color="red", order=0, can_access_dashboard=True, can_moderate_forum=True,
                   free_access_paid=True, can_see_test_builds=True,
                   description="Управление сайтом, модерация форума, все продукты бесплатно"),
    "testers": dict(title="Тестеры", color="orange", order=5, free_access_paid=True, can_see_test_builds=True,
                    description="Бесплатный доступ к платным продуктам и тестовым сборкам"),
    "players": dict(title="Игроки", color="green", order=10, is_default=True,
                    description="Покупают и скачивают продукты; сюда попадают новые пользователи"),
}


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Role = apps.get_model("accounts", "Role")
    for name, data in DEFAULTS.items():
        group, _ = Group.objects.get_or_create(name=name)
        Role.objects.get_or_create(group=group, defaults=data)


def remove_roles(apps, schema_editor):
    apps.get_model("accounts", "Role").objects.filter(group__name__in=DEFAULTS).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_role")]
    operations = [migrations.RunPython(create_roles, remove_roles)]
