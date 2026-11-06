"""Сброс пароля по e-mail на основе стандартных представлений Django.

Безопасность:
* Страница «письмо отправлено» одинакова, есть такой e-mail или нет — по ней нельзя узнать,
  зарегистрирован ли адрес.
* Ссылка одноразовая (токен становится недействительным после смены пароля) и живёт
  PASSWORD_RESET_TIMEOUT секунд.
* Ограничение частоты: не больше RESET_LIMIT_PER_IP запросов в час с одного IP и
  RESET_LIMIT_PER_EMAIL писем в час на один адрес.
* После смены пароля пользователю приходит уведомление, а все его сессии на других
  устройствах завершаются (Django меняет хэш сессии).
"""
import logging

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

log = logging.getLogger(__name__)

RESET_LIMIT_PER_IP = 5
RESET_LIMIT_PER_EMAIL = 3
RESET_WINDOW = 3600


def _hit(key, limit):
    """Увеличивает счётчик; возвращает True, если лимит уже исчерпан."""
    cache.add(key, 0, RESET_WINDOW)
    try:
        count = cache.incr(key)
    except ValueError:  # ключ успел истечь
        cache.set(key, 1, RESET_WINDOW)
        count = 1
    return count > limit


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/email/password_reset.txt"
    html_email_template_name = "accounts/email/password_reset.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    extra_email_context = {"site_name": "TechVault"}

    def form_valid(self, form):
        ip = self.request.META.get("REMOTE_ADDR", "")
        email = form.cleaned_data["email"].strip().lower()
        ip_blocked = _hit(f"pwreset:ip:{ip}", RESET_LIMIT_PER_IP)
        email_blocked = _hit(f"pwreset:email:{email}", RESET_LIMIT_PER_EMAIL)
        if ip_blocked:
            form.add_error(None, _("Слишком много запросов. Попробуйте снова через час."))
            return self.form_invalid(form)
        if email_blocked:
            # Не сообщаем об этом пользователю, чтобы не раскрывать, есть ли такой адрес
            log.warning("Лимит писем сброса пароля исчерпан для адреса")
            return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if user.email:
            context = {"user": user, "site_name": "TechVault",
                       "login_url": self.request.build_absolute_uri(str(reverse_lazy("accounts:login"))),
                       "contact_url": self.request.build_absolute_uri(str(reverse_lazy("core:contact")))}
            send_mail(
                subject=_("Пароль на TechVault изменён"),
                message=render_to_string("accounts/email/password_changed.txt", context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        return response


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
