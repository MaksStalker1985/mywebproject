from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts import roles

from . import access
from .forms import PostForm, TopicForm
from .models import Category, Post, Topic

POSTS_PER_PAGE = 15

# Весь форум доступен только авторизованным пользователям (@login_required);
# доступ к разделам настраивается по группам (forum/access.py).


@login_required
def index(request):
    categories = access.visible_categories(request.user, Category.objects).annotate(
        topic_count=Count("topics", distinct=True),
        post_count=Count("topics__posts", distinct=True),
        last_post=Max("topics__last_activity"),
    ).order_by("order", "title")
    for c in categories:
        c.can_write = access.can_write(request.user, c)
    return render(request, "forum/index.html", {"categories": categories})


def _category_or_404(user, slug):
    cat = get_object_or_404(Category, slug=slug)
    if not access.can_read(user, cat):
        raise Http404
    return cat


@login_required
def category(request, slug):
    cat = _category_or_404(request.user, slug)
    topics = cat.topics.select_related("author__profile").annotate(reply_count=Count("posts")).order_by("-is_pinned", "-last_activity")
    page = Paginator(topics, 20).get_page(request.GET.get("page"))
    return render(request, "forum/category.html", {
        "category": cat, "page": page, "can_write": access.can_write(request.user, cat)})


@login_required
def topic_detail(request, pk):
    topic = get_object_or_404(Topic.objects.select_related("category", "author"), pk=pk)
    if not access.can_read(request.user, topic.category):
        raise Http404
    can_moderate = roles.can_moderate(request.user)
    can_write = access.can_write(request.user, topic.category)
    can_reply = can_write and (not topic.is_locked or can_moderate)
    form = PostForm(request.POST or None)
    if request.method == "POST":
        if not can_reply:
            raise PermissionDenied
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            Topic.objects.filter(pk=topic.pk).update(last_activity=timezone.now())
            page_num = (topic.posts.count() - 1) // POSTS_PER_PAGE + 1
            return redirect(f"{topic.get_absolute_url()}?page={page_num}#post-{post.pk}")

    page = Paginator(topic.posts.select_related("author__profile"), POSTS_PER_PAGE).get_page(request.GET.get("page"))
    for post in page:
        post.author_is_team = roles.can_moderate(post.author)
    return render(request, "forum/topic.html", {
        "topic": topic, "page": page, "form": form,
        "can_reply": can_reply, "can_write": can_write, "can_moderate": can_moderate,
    })


@login_required
def topic_create(request, slug):
    cat = _category_or_404(request.user, slug)
    if not access.can_write(request.user, cat):
        raise PermissionDenied
    form = TopicForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            topic = Topic.objects.create(category=cat, title=form.cleaned_data["title"], author=request.user)
            Post.objects.create(topic=topic, author=request.user, body=form.cleaned_data["body"])
        messages.success(request, _("Тема создана."))
        return redirect(topic)
    return render(request, "forum/topic_form.html", {"category": cat, "form": form})


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post.objects.select_related("topic__category"), pk=pk)
    if not access.can_read(request.user, post.topic.category):
        raise Http404
    if post.author != request.user and not roles.can_moderate(request.user):
        raise PermissionDenied
    topic = post.topic
    if topic.posts.first() == post:
        # Удаление первого сообщения удаляет всю тему
        category = topic.category
        topic.delete()
        messages.info(request, _("Тема удалена."))
        return redirect(category)
    post.delete()
    messages.info(request, _("Сообщение удалено."))
    return redirect(topic)
