from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label=_("E-mail"), required=True)
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={"required": _("Для регистрации нужно принять условия.")},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accept_terms"].label = mark_safe(
            _("Я принимаю <a href=\"%(terms)s\" target=\"_blank\">условия использования</a> и "
              "<a href=\"%(privacy)s\" target=\"_blank\">политику конфиденциальности</a>")
            % {"terms": reverse_lazy("core:page", args=["terms"]),
               "privacy": reverse_lazy("core:page", args=["privacy"])}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Пользователь с таким e-mail уже зарегистрирован."))
        return email
