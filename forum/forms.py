from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Topic


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["body"]
        labels = {"body": _("Ваш ответ")}
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class TopicForm(forms.Form):
    kind = forms.ChoiceField(
        label=_("Тип публикации"), choices=Topic.Kind.choices, initial=Topic.Kind.DISCUSSION, required=False,
        widget=forms.RadioSelect,
        help_text=_("Вопрос — участники отвечают, а вы отмечаете ответ, который помог."),
    )
    subforum = forms.ModelChoiceField(label=_("Подтема"), queryset=None, required=False, empty_label=None)
    title = forms.CharField(label=_("Заголовок"), max_length=200)
    body = forms.CharField(label=_("Текст"), widget=forms.Textarea(attrs={"rows": 8}))

    def __init__(self, *args, category, subforum=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        if subforum is not None:
            # Подтема уже выбрана адресом страницы
            del self.fields["subforum"]
            self.fixed_subforum = subforum
        else:
            self.fixed_subforum = None
            subforums = category.subforums.order_by("order", "title")
            if subforums.exists():
                self.fields["subforum"].queryset = subforums
            else:
                del self.fields["subforum"]

    def clean_kind(self):
        return self.cleaned_data.get("kind") or Topic.Kind.DISCUSSION

    def get_subforum(self):
        return self.fixed_subforum or self.cleaned_data.get("subforum") or self.category.default_subforum()
