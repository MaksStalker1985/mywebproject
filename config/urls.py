from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static as static_url
from django.views.generic import RedirectView
from django.urls import include, path

from core import views as core_views
from core.sitemaps import SITEMAPS
from payments import views as payments_views

urlpatterns = [
    # Переключение языка (POST с полем language)
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="django.contrib.sitemaps.views.sitemap"),
    path("favicon.ico", RedirectView.as_view(url=static_url("img/favicon.svg"), permanent=True)),
    # Уведомления от Stripe — без языкового префикса
    path("payments/webhook/stripe/", payments_views.stripe_webhook, name="stripe_webhook"),
    path("payments/webhook/paddle/", payments_views.paddle_webhook, name="paddle_webhook"),
    # Укажите этот адрес в Paddle → Checkout settings → Default payment link
    path("payments/paddle/pay/", payments_views.paddle_payment_link, name="paddle_payment_link"),
]

# Все страницы сайта получают префикс языка: /ru/, /en/, /uk/
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("catalog/", include("catalog.urls")),
    path("forum/", include("forum.urls")),
    path("accounts/", include("accounts.urls")),
    path("payments/", include("payments.urls")),
    path("manage/", include("dashboard.urls")),
)

if settings.DEBUG:
    # Публичны только обложки и аватары; установочные файлы (downloads/) выдаются после проверки покупки
    for public_dir in ("covers", "avatars"):
        urlpatterns += static(f"{settings.MEDIA_URL}{public_dir}/", document_root=settings.MEDIA_ROOT / public_dir)
