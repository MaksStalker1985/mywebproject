"""Группы пользователей и их права.

Группа — стандартная `auth.Group` с настройками в `accounts.Role`. Администратор сайта создаёт
и редактирует группы в панели управления: права (панель, модерация, бесплатный доступ к платным
продуктам, тестовые сборки) и доступ к каждому разделу форума (`forum.CategoryAccess`).

Пользователь состоит в одной группе. Суперпользователь имеет все права независимо от группы.
Флаг `is_staff` синхронизируется с правом «панель управления» (см. `sync_staff`).
"""
from django.contrib.auth.models import Group, User

ADMINS = "admins"
TESTERS = "testers"
PLAYERS = "players"

PERMISSIONS = ["can_access_dashboard", "can_moderate_forum", "free_access_paid", "can_see_test_builds"]


def _roles():
    from .models import Role

    return Role.objects.select_related("group")


def all_roles():
    return list(_roles())


def default_role():
    return _roles().filter(is_default=True).first() or _roles().filter(group__name=PLAYERS).first()


def get_role(user):
    """Группа пользователя (объект Role) или None для анонимного. Результат кешируется на объекте."""
    if user is None or not user.is_authenticated:
        return None
    if not hasattr(user, "_role_cache"):
        role = _roles().filter(group__user=user).first()
        if user.is_superuser:
            role = _roles().filter(group__name=ADMINS).first() or role
        user._role_cache = role or default_role()
    return user._role_cache


def has_perm(user, perm):
    if perm not in PERMISSIONS:
        raise ValueError(perm)
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = get_role(user)
    return bool(role and getattr(role, perm))


def is_admin(user):
    return has_perm(user, "can_access_dashboard")


def can_moderate(user):
    return has_perm(user, "can_moderate_forum")


def has_free_access(user):
    return has_perm(user, "free_access_paid")


def can_see_test_builds(user):
    return has_perm(user, "can_see_test_builds")


def _resolve(role):
    from .models import Role

    if isinstance(role, Role):
        return role
    try:
        return _roles().get(group__name=role)
    except Role.DoesNotExist:
        raise ValueError(role) from None


def set_role(user, role):
    """Оставляет пользователя ровно в одной группе и синхронизирует is_staff."""
    role = _resolve(role)
    user.groups.remove(*Group.objects.filter(role__isnull=False).exclude(pk=role.group_id))
    user.groups.add(role.group)
    user.__dict__.pop("_role_cache", None)
    sync_staff(User.objects.filter(pk=user.pk))
    user.refresh_from_db(fields=["is_staff"])


def sync_staff(users):
    """is_staff = суперпользователь или группа с правом «панель управления»."""
    for user in users:
        user.__dict__.pop("_role_cache", None)
        should_be_staff = is_admin(user)
        if user.is_staff != should_be_staff:
            User.objects.filter(pk=user.pk).update(is_staff=should_be_staff)
            user.is_staff = should_be_staff
