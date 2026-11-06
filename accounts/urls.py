from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import password_reset, views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("cabinet/orders/", views.order_history, name="orders"),
    path("profile/", views.profile, name="profile"),
    path("profile/avatar/", views.avatar_update, name="avatar_update"),
    path("profile/avatar/remove/", views.avatar_remove, name="avatar_remove"),
    path(
        "password/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:profile"),
        ),
        name="password_change",
    ),
    # Сброс пароля по e-mail
    path("password/reset/", password_reset.PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/sent/", password_reset.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", password_reset.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path("password/reset/complete/", password_reset.PasswordResetCompleteView.as_view(),
         name="password_reset_complete"),
]
