from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["body"]
        labels = {"body": _("Ваш ответ")}
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class TopicForm(forms.Form):
    title = forms.CharField(label=_("Заголовок"), max_length=200)
    body = forms.CharField(label=_("Сообщение"), widget=forms.Textarea(attrs={"rows": 8}))
