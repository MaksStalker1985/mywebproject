"""Создаёт группы «Администраторы», «Тестеры», «Игроки» и распределяет существующих пользователей."""
from django.db import migrations

ROLE_GROUPS = ["admins", "testers", "players"]


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")
    groups = {name: Group.objects.get_or_create(name=name)[0] for name in ROLE_GROUPS}
    for user in User.objects.all():
        if user.groups.filter(name__in=ROLE_GROUPS).exists():
            continue
        user.groups.add(groups["admins"] if (user.is_staff or user.is_superuser) else groups["players"])


def remove_groups(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(create_groups, remove_groups)]
