from django.apps import AppConfig
from django.core import checks


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        checks.register(check_paddle_settings, "payments")


def check_paddle_settings(app_configs, **kwargs):
    """Предупреждения (не ошибки — чтобы не мешать обновлению) о неполной настройке Paddle."""
    from django.conf import settings

    from .providers import paddle_config_problems

    if settings.PAYMENTS_PROVIDER != "paddle":
        return []
    return [checks.Warning(f"Paddle: {p}", hint="Подробнее: techvault-manage paddle check", id="payments.W001")
            for p in paddle_config_problems()]
