from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = _("Учётные записи")

    def ready(self):
        from . import signals

        post_migrate.connect(signals.grant_admin_permissions, sender=self)
