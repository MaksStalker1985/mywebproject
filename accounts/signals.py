from django.contrib.auth.models import Group, Permission, User
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from . import roles
from .models import Role

ADMIN_PERMISSION_APPS = ["catalog", "core", "forum", "payments", "auth", "accounts"]


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, raw=False, **kwargs):
    """Новый пользователь попадает в группу по умолчанию; суперпользователь или созданный с is_staff — в администраторы."""
    if not created or raw:
        return
    role = None
    if instance.is_superuser or instance.is_staff:
        role = Role.objects.filter(group__name=roles.ADMINS).first()
    role = role or roles.default_role()
    if role:
        instance.groups.add(role.group)


@receiver(m2m_changed, sender=User.groups.through)
def sync_staff_flag(sender, instance, action, reverse, pk_set, **kwargs):
    """Флаг is_staff (вход в панель и Django admin) следует за правами группы."""
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    if not reverse:
        roles.sync_staff([instance])
    else:
        roles.sync_staff(User.objects.filter(pk__in=pk_set) if pk_set else User.objects.filter(is_staff=True))


def grant_model_permissions(role):
    perms = Permission.objects.filter(content_type__app_label__in=ADMIN_PERMISSION_APPS)
    if role.can_access_dashboard:
        role.group.permissions.add(*perms)
    else:
        role.group.permissions.remove(*perms)


@receiver(post_save, sender=Role)
def role_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    if instance.is_default:
        Role.objects.exclude(pk=instance.pk).filter(is_default=True).update(is_default=False)
    grant_model_permissions(instance)
    roles.sync_staff(instance.group.user_set.all())


def grant_admin_permissions(sender, **kwargs):
    """После migrate выдаёт права на модели (для Django admin) группам с доступом к панели."""
    for role in Role.objects.select_related("group"):
        grant_model_permissions(role)
