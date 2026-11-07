"""Панель управления контентом для группы «Администраторы»."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Prefetch, ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from accounts import roles
from catalog.models import Product
from core.models import ContactMessage, Page
from forum.models import Category, Subforum, Topic
from payments.models import Order

from accounts.models import Role

from .forms import CategoryForm, PageForm, ProductForm, RoleForm, SubforumForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Пускает только администраторов; анонимных отправляет на вход, остальным — 403."""

    def test_func(self):
        return roles.is_admin(self.request.user)


class SuccessMessageMixin:
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message % {"obj": self.object})
        return response


# --- Обзор ---

class IndexView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        paid = Order.objects.filter(status=Order.Status.PAID)
        return super().get_context_data(
            stats={
                "games": Product.objects.filter(kind=Product.Kind.GAME).count(),
                "software": Product.objects.filter(kind=Product.Kind.SOFTWARE).count(),
                "users": User.objects.count(),
                "sales": paid.count(),
                "revenue": paid.aggregate(s=Sum("amount"))["s"] or 0,
                "new_messages": ContactMessage.objects.filter(is_processed=False).count(),
                "downloads": Product.objects.aggregate(s=Sum("download_count"))["s"] or 0,
                "currency": settings.PAYMENTS_CURRENCY,
            },
            top_products=Product.objects.annotate(sales=Count("orders", filter=Q(orders__status="paid")))
            .order_by("-sales", "-download_count")[:5],
            recent_orders=Order.objects.select_related("user", "product")[:5],
            recent_messages=ContactMessage.objects.filter(is_processed=False)[:5],
            **kwargs,
        )


# --- Игры и ПО ---

class ProductListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/product_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.annotate(sales=Count("orders", filter=Q(orders__status="paid"))).order_by("-created_at")
        if q := self.request.GET.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(developer__icontains=q))
        if kind := self.request.GET.get("kind"):
            qs = qs.filter(kind=kind)
        return qs


class ProductFormMixin:
    """Форма продукта: передаёт пользователя (для проверки загрузки) и прикрепляет файл,
    загруженный по частям."""

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def get_context_data(self, **kwargs):
        upload_i18n = {
            "cancel": _("Отменить"), "pause": _("Пауза"), "resume": _("Продолжить"), "paused": _("Пауза"),
            "uploading": _("Загрузка…"), "retry": _("Нет связи — повтор…"),
            "done": _("Загружено. Нажмите «Сохранить»."), "left": _("осталось"),
            "failed": _("Не удалось загрузить файл."), "offline": _("Нет связи с сервером."),
            "lost": _("Загрузка не найдена на сервере — выберите файл ещё раз."), "http": _("Ошибка сервера"),
            "wait": _("Файл ещё загружается. Дождитесь окончания загрузки и нажмите «Сохранить»."),
            "b": _("Б"), "kb": _("КБ"), "mb": _("МБ"), "gb": _("ГБ"), "sec": _("с"), "min": _("мин"), "hour": _("ч"),
        }
        return super().get_context_data(chunked_upload=True, upload_i18n=upload_i18n, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.upload is not None:
            from .uploads import attach_upload
            attach_upload(form.upload, self.object)
        return response


class ProductCreateView(StaffRequiredMixin, ProductFormMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:products")
    success_message = gettext_lazy("«%(obj)s» добавлен в каталог.")
    extra_context = {"heading": gettext_lazy("Новый продукт"), "back_url": reverse_lazy("dashboard:products")}


class ProductUpdateView(StaffRequiredMixin, ProductFormMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:products")
    success_message = gettext_lazy("Изменения в «%(obj)s» сохранены.")
    extra_context = {"back_url": reverse_lazy("dashboard:products"), "delete_url_name": "dashboard:product_delete"}


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:products")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, _("У продукта есть заказы, удалить его нельзя. Снимите его с публикации."))
            return redirect("dashboard:product_edit", self.object.pk)
        messages.success(self.request, _("Продукт удалён."))
        return response


# --- Форум ---

class CategoryListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/category_list.html"
    queryset = Category.objects.annotate(topic_count=Count("topics")).prefetch_related(
        Prefetch("subforums", queryset=Subforum.objects.annotate(topic_count=Count("topics")).order_by("order", "title"))
    ).order_by("order", "title")


class CategoryCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:categories")
    success_message = gettext_lazy("Главная тема «%(obj)s» создана.")
    extra_context = {"heading": gettext_lazy("Новая главная тема"), "back_url": reverse_lazy("dashboard:categories")}


class CategoryUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:categories")
    success_message = gettext_lazy("Главная тема «%(obj)s» сохранена.")
    extra_context = {"back_url": reverse_lazy("dashboard:categories"), "delete_url_name": "dashboard:category_delete"}


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:categories")


class SubforumCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Subforum
    form_class = SubforumForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:categories")
    success_message = gettext_lazy("Подтема «%(obj)s» создана.")
    extra_context = {"heading": gettext_lazy("Новая подтема"), "back_url": reverse_lazy("dashboard:categories")}

    def get_initial(self):
        return {"category": self.request.GET.get("category")}


class SubforumUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Subforum
    form_class = SubforumForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:categories")
    success_message = gettext_lazy("Подтема «%(obj)s» сохранена.")
    extra_context = {"back_url": reverse_lazy("dashboard:categories"), "delete_url_name": "dashboard:subforum_delete"}


class SubforumDeleteView(StaffRequiredMixin, DeleteView):
    model = Subforum
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:categories")


class TopicListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/topic_list.html"
    paginate_by = 30
    queryset = Topic.objects.select_related("category", "subforum", "author").annotate(post_count=Count("posts")).order_by(
        "-is_pinned", "-last_activity"
    )


class TopicToggleView(StaffRequiredMixin, View):
    """Закрепить/открепить или закрыть/открыть тему."""

    def post(self, request, pk, field):
        if field not in {"is_pinned", "is_locked"}:
            return redirect("dashboard:topics")
        topic = get_object_or_404(Topic, pk=pk)
        setattr(topic, field, not getattr(topic, field))
        topic.save(update_fields=[field])
        return redirect(request.POST.get("next") or "dashboard:topics")


class TopicDeleteView(StaffRequiredMixin, DeleteView):
    model = Topic
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:topics")


# --- Обращения и заказы ---

class MessageListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/message_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = ContactMessage.objects.select_related("product")
        if self.request.GET.get("show") != "all":
            qs = qs.filter(is_processed=False)
        return qs


class MessageToggleView(StaffRequiredMixin, View):
    def post(self, request, pk):
        msg = get_object_or_404(ContactMessage, pk=pk)
        msg.is_processed = not msg.is_processed
        msg.save(update_fields=["is_processed"])
        return redirect(request.POST.get("next") or "dashboard:messages")


# --- Пользователи и группы ---

class UserListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/user_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = User.objects.select_related("profile").prefetch_related("groups").annotate(
            purchases=Count("orders", filter=Q(orders__status=Order.Status.PAID))
        ).order_by("-date_joined")
        if q := self.request.GET.get("q", "").strip():
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        if role := self.request.GET.get("role"):
            qs = qs.filter(groups__name=role)
        return qs

    def get_context_data(self, **kwargs):
        all_roles = Role.objects.select_related("group").annotate(members=Count("group__user"))
        ctx = super().get_context_data(roles=all_roles, **kwargs)
        for u in ctx["page_obj"]:
            u.role = roles.get_role(u)
        return ctx


class UserRoleView(StaffRequiredMixin, View):
    """Перевод пользователя в другую группу."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        role = Role.objects.select_related("group").filter(group__name=request.POST.get("role")).first()
        if role is None:
            messages.error(request, _("Неизвестная группа."))
        elif user == request.user:
            messages.error(request, _("Нельзя изменить собственную группу."))
        elif user.is_superuser:
            messages.error(request, _("Суперпользователь всегда остаётся администратором."))
        else:
            roles.set_role(user, role)
            messages.success(request, _("%(user)s теперь в группе «%(role)s».") % {
                "user": user.username, "role": role.display_title})
        return redirect(request.POST.get("next") or "dashboard:users")


class UserAvatarDeleteView(StaffRequiredMixin, View):
    """Удаление неподходящего аватара пользователя."""

    def post(self, request, pk):
        from accounts.avatars import delete_avatar

        user = get_object_or_404(User, pk=pk)
        delete_avatar(user)
        messages.info(request, _("Аватар пользователя %(user)s удалён.") % {"user": user.username})
        return redirect(request.POST.get("next") or "dashboard:users")


class RoleListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/role_list.html"

    def get_queryset(self):
        return Role.objects.select_related("group").annotate(
            members=Count("group__user", distinct=True),
            restricted=Count("forum_access", filter=~Q(forum_access__level="write"), distinct=True),
        ).order_by("order", "pk")

    def get_context_data(self, **kwargs):
        return super().get_context_data(category_count=Category.objects.count(), **kwargs)


class RoleCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "dashboard/role_form.html"
    success_url = reverse_lazy("dashboard:roles")
    success_message = gettext_lazy("Группа «%(obj)s» создана.")
    extra_context = {"heading": gettext_lazy("Новая группа")}


class RoleUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = "dashboard/role_form.html"
    success_url = reverse_lazy("dashboard:roles")
    success_message = gettext_lazy("Группа «%(obj)s» сохранена.")


class RoleDeleteView(StaffRequiredMixin, View):
    """Удаление группы: её участники переходят в группу по умолчанию."""

    template_name = "dashboard/role_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.role = get_object_or_404(Role.objects.select_related("group"), pk=kwargs["pk"])
        if not self.role.can_delete:
            messages.error(request, _("Эту группу нельзя удалить: это группа администраторов или группа по умолчанию."))
            return redirect("dashboard:role_edit", self.role.pk)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        return render(request, self.template_name, {
            "role": self.role, "members": self.role.group.user_set.count(), "default_role": roles.default_role(),
        })

    def post(self, request, pk):
        default = roles.default_role()
        with transaction.atomic():
            for user in list(self.role.group.user_set.all()):
                roles.set_role(user, default)
            title = self.role.display_title
            self.role.group.delete()  # каскадом удаляет Role и правила доступа к форуму
        messages.success(request, _("Группа «%(role)s» удалена, её участники перенесены в «%(default)s».") % {
            "role": title, "default": default.display_title})
        return redirect("dashboard:roles")


# --- Информационные страницы ---

class PageListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/page_list.html"
    queryset = Page.objects.order_by("order", "slug")


class PageCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:pages")
    success_message = gettext_lazy("Страница «%(obj)s» создана.")
    extra_context = {"heading": gettext_lazy("Новая страница"), "back_url": reverse_lazy("dashboard:pages")}


class PageUpdateView(StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Page
    form_class = PageForm
    template_name = "dashboard/form.html"
    success_url = reverse_lazy("dashboard:pages")
    success_message = gettext_lazy("Страница «%(obj)s» сохранена.")
    extra_context = {"back_url": reverse_lazy("dashboard:pages"), "delete_url_name": "dashboard:page_delete"}


class PageDeleteView(StaffRequiredMixin, DeleteView):
    model = Page
    template_name = "dashboard/confirm_delete.html"
    success_url = reverse_lazy("dashboard:pages")


class OrderRefundView(StaffRequiredMixin, View):
    """Отметить оплаченный заказ как возвращённый — доступ к скачиванию закрывается.
    Сами деньги возвращаются в кабинете Paddle/Stripe."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status == Order.Status.PAID:
            Order.objects.filter(pk=pk, status=Order.Status.PAID).update(status=Order.Status.REFUNDED)
            messages.success(request, _("Заказ #%(pk)s отмечен как возвращённый. Не забудьте вернуть деньги "
                                        "в кабинете платёжной системы.") % {"pk": pk})
        return redirect(request.POST.get("next") or "dashboard:orders")


class OrderListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/order_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = Order.objects.select_related("user", "product")
        if status := self.request.GET.get("status"):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        return super().get_context_data(statuses=Order.Status.choices, **kwargs)
