import uuid

from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from accounts.models import Role
from catalog.models import Product, Upload
from core.models import Page
from forum.models import Category, CategoryAccess, Subforum


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "kind", "title", "slug", "genre", "short_description", "description", "developer",
            "version", "release_stage", "platform", "price", "cover", "file", "changelog", "system_requirements",
            "is_featured", "is_published", "for_testers",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 10}),
            "changelog": forms.Textarea(attrs={"rows": 6}),
            "system_requirements": forms.Textarea(attrs={"rows": 6}),
        }
        help_texts = {"slug": _("Часть адреса страницы. Оставьте пустым — заполнится из названия.")}

    # Файл, загруженный по частям (static/js/chunked-upload.js); заменяет поле «файл»
    upload_id = forms.UUIDField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.upload = None
        self.fields["slug"].required = False
        self.fields["file"].help_text = _(
            "Большие файлы загружаются по частям с индикатором прогресса; при обрыве связи загрузка "
            "продолжится. Можно сохранять форму после того, как загрузка завершится.")

    def clean_upload_id(self):
        upload_id = self.cleaned_data.get("upload_id")
        if not upload_id:
            return None
        upload = Upload.objects.filter(pk=upload_id, user=self.user).first()
        if upload is None:
            raise forms.ValidationError(_("Загрузка файла не найдена — выберите файл ещё раз."))
        if not upload.is_complete:
            raise forms.ValidationError(_("Файл ещё загружается — дождитесь окончания загрузки."))
        self.upload = upload
        return upload_id

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("title", "")) or uuid.uuid4().hex[:8]
        clash = Product.objects.filter(slug=slug).exclude(pk=self.instance.pk)
        if clash.exists():
            if self.cleaned_data.get("slug"):
                raise forms.ValidationError(_("Такой адрес уже занят."))
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
        return slug


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["title", "slug", "description", "order"]


class SubforumForm(forms.ModelForm):
    class Meta:
        model = Subforum
        fields = ["category", "title", "slug", "description", "order"]
        help_texts = {"slug": _("Латиница, цифры и дефис; уникален внутри главной темы.")}

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if slug == "new":
            raise forms.ValidationError(_("Этот адрес зарезервирован, выберите другой."))
        return slug

    def clean(self):
        data = super().clean()
        cat, slug = data.get("category"), data.get("slug")
        if cat and slug and Subforum.objects.filter(category=cat, slug=slug).exclude(pk=self.instance.pk).exists():
            self.add_error("slug", _("В этой главной теме уже есть подтема с таким адресом."))
        return data


class RoleForm(forms.ModelForm):
    """Группа пользователей: название, права и доступ к каждому разделу форума."""

    key = forms.SlugField(
        label=_("Ключ"), max_length=150, required=False,
        help_text=_("Латиница, цифры и дефис. Оставьте пустым — будет создан автоматически."),
    )

    PERMISSION_FIELDS = ["can_access_dashboard", "can_moderate_forum", "free_access_paid", "can_see_test_builds",
                         "is_default"]

    class Meta:
        model = Role
        fields = ["title", "key", "description", "color", "order", "can_access_dashboard", "can_moderate_forum",
                  "free_access_paid", "can_see_test_builds", "is_default"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["key"].initial = self.instance.group.name
            if self.instance.is_system:
                self.fields["key"].disabled = True
                self.fields["can_access_dashboard"].disabled = True
                self.fields["can_access_dashboard"].help_text = _(
                    "Группа «Администраторы» всегда имеет доступ к панели, чтобы не потерять управление сайтом.")
        levels = {}
        if self.instance.pk:
            levels = dict(self.instance.forum_access.values_list("category_id", "level"))
        self.categories = list(Category.objects.order_by("order", "title"))
        for cat in self.categories:
            self.fields[f"forum_{cat.pk}"] = forms.ChoiceField(
                label=cat.title, choices=CategoryAccess.Level.choices,
                initial=levels.get(cat.pk, CategoryAccess.Level.WRITE),
            )

    # Группы полей для шаблона
    def main_fields(self):
        return [self[name] for name in ["title", "key", "description", "color", "order"]]

    def permission_fields(self):
        return [self[name] for name in self.PERMISSION_FIELDS]

    def forum_fields(self):
        return [(cat, self[f"forum_{cat.pk}"]) for cat in self.categories]

    def clean_key(self):
        if self.instance.pk and self.instance.is_system:
            return self.instance.group.name
        key = self.cleaned_data.get("key") or slugify(self.cleaned_data.get("title", "")) or f"group-{uuid.uuid4().hex[:6]}"
        clash = Group.objects.filter(name=key)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.group_id)
        if clash.exists():
            raise forms.ValidationError(_("Группа с таким ключом уже есть."))
        return key

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk and self.instance.is_default and not cleaned.get("is_default"):
            self.add_error("is_default", _("Должна остаться группа по умолчанию. Назначьте её в другой группе."))
        if self.instance.pk and self.instance.is_system:
            cleaned["can_access_dashboard"] = True
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        role = super().save(commit=False)
        key = self.cleaned_data["key"]
        if role.pk:
            group = role.group
            if group.name != key:
                group.name = key
                group.save(update_fields=["name"])
        else:
            role.group = Group.objects.create(name=key)
        role.save()
        for cat in self.categories:
            level = self.cleaned_data[f"forum_{cat.pk}"]
            if level == CategoryAccess.Level.WRITE:
                CategoryAccess.objects.filter(role=role, category=cat).delete()
            else:
                CategoryAccess.objects.update_or_create(role=role, category=cat, defaults={"level": level})
        return role


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["slug", "order", "title_ru", "title_en", "title_uk", "body_ru", "body_en", "body_uk",
                  "show_in_footer", "is_published"]
        widgets = {f"body_{lang}": forms.Textarea(attrs={"rows": 14}) for lang in ("ru", "en", "uk")}
        help_texts = {
            "body_ru": _("Пустая строка — новый абзац, «## » в начале строки — подзаголовок, «- » — пункт списка. "
                         "Ссылки и e-mail становятся кликабельными."),
            "body_en": _("Пусто — показывается русский текст."),
            "body_uk": _("Пусто — показывается русский текст."),
        }
