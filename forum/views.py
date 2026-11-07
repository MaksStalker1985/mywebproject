from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts import roles
from core.images import save_image

from . import access
from .forms import PostForm, TopicForm
from .models import Category, Post, PostImage, Subforum, Topic

POSTS_PER_PAGE = 15


def _save_post_images(post, processed_images):
    for processed in processed_images or []:
        save_image(PostImage(post=post), processed)
TOPICS_PER_PAGE = 20

# Структура: главная тема (Category) → подтема (Subforum) → публикация (Topic: обсуждение или вопрос)
# → сообщения (Post). Весь форум доступен только авторизованным пользователям; доступ групп
# настраивается на уровне главной темы (forum/access.py) и действует на все её подтемы.


def _subforums_with_stats():
    return Subforum.objects.annotate(
        topic_count=Count("topics", distinct=True),
        post_count=Count("topics__posts", distinct=True),
        last_post=Max("topics__last_activity"),
    ).order_by("order", "title")


def _last_topics(subforums):
    """Последняя активная публикация каждой подтемы — для колонки «Последнее»."""
    for sub in subforums:
        sub.last_topic = sub.topics.select_related("author__profile").order_by("-last_activity").first()


@login_required
def index(request):
    categories = list(
        access.visible_categories(request.user, Category.objects)
        .prefetch_related(Prefetch("subforums", queryset=_subforums_with_stats()))
        .order_by("order", "title")
    )
    for c in categories:
        c.can_write = access.can_write(request.user, c)
        c.subforum_list = list(c.subforums.all())
        _last_topics(c.subforum_list)
    return render(request, "forum/index.html", {"categories": categories})


def _category_or_404(user, slug):
    cat = get_object_or_404(Category, slug=slug)
    if not access.can_read(user, cat):
        raise Http404
    return cat


@login_required
def category(request, slug):
    cat = _category_or_404(request.user, slug)
    subforums = list(_subforums_with_stats().filter(category=cat))
    _last_topics(subforums)
    recent = (cat.topics.select_related("author__profile", "subforum")
              .annotate(reply_count=Count("posts")).order_by("-last_activity")[:8])
    return render(request, "forum/category.html", {
        "category": cat, "subforums": subforums, "recent": recent,
        "can_write": access.can_write(request.user, cat),
    })


TOPIC_FILTERS = {
    "discussion": Q(kind=Topic.Kind.DISCUSSION),
    "question": Q(kind=Topic.Kind.QUESTION),
    "unsolved": Q(kind=Topic.Kind.QUESTION, solution__isnull=True),
}


@login_required
def subforum(request, slug, sub):
    cat = _category_or_404(request.user, slug)
    sub = get_object_or_404(Subforum, category=cat, slug=sub)
    topics = sub.topics.select_related("author__profile", "solution").annotate(reply_count=Count("posts"))
    show = request.GET.get("show", "")
    if show in TOPIC_FILTERS:
        topics = topics.filter(TOPIC_FILTERS[show])
    topics = topics.order_by("-is_pinned", "-last_activity")
    page = Paginator(topics, TOPICS_PER_PAGE).get_page(request.GET.get("page"))
    return render(request, "forum/subforum.html", {
        "category": cat, "subforum": sub, "page": page, "show": show,
        "can_write": access.can_write(request.user, cat),
    })


def _create_topic(request, cat, sub=None):
    if not access.can_write(request.user, cat):
        raise PermissionDenied
    initial = {"kind": request.GET.get("kind")} if request.GET.get("kind") in Topic.Kind.values else {}
    if sub is None and request.GET.get("sub"):
        initial["subforum"] = cat.subforums.filter(slug=request.GET["sub"]).first()
    form = TopicForm(request.POST or None, request.FILES or None, category=cat, subforum=sub, initial=initial)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            topic = Topic.objects.create(
                subforum=form.get_subforum(), kind=form.cleaned_data["kind"],
                title=form.cleaned_data["title"], author=request.user,
            )
            post = Post.objects.create(topic=topic, author=request.user, body=form.cleaned_data["body"])
            _save_post_images(post, form.cleaned_data.get("images"))
        messages.success(request, _("Вопрос опубликован.") if topic.is_question else _("Публикация создана."))
        return redirect(topic)
    return render(request, "forum/topic_form.html", {"category": cat, "subforum": sub, "form": form})


@login_required
def topic_create(request, slug):
    """Новая публикация в главной теме — подтема выбирается в форме."""
    return _create_topic(request, _category_or_404(request.user, slug))


@login_required
def subforum_topic_create(request, slug, sub):
    cat = _category_or_404(request.user, slug)
    return _create_topic(request, cat, get_object_or_404(Subforum, category=cat, slug=sub))


def _can_mark_solution(user, topic):
    return topic.is_question and (user == topic.author or roles.can_moderate(user))


@login_required
def topic_detail(request, pk):
    topic = get_object_or_404(Topic.objects.select_related("category", "subforum", "author"), pk=pk)
    if not access.can_read(request.user, topic.category):
        raise Http404
    can_moderate = roles.can_moderate(request.user)
    can_write = access.can_write(request.user, topic.category)
    can_reply = can_write and (not topic.is_locked or can_moderate)
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if not can_reply:
            raise PermissionDenied
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            _save_post_images(post, form.cleaned_data.get("images"))
            Topic.objects.filter(pk=topic.pk).update(last_activity=timezone.now())
            page_num = (topic.posts.count() - 1) // POSTS_PER_PAGE + 1
            return redirect(f"{topic.get_absolute_url()}?page={page_num}#post-{post.pk}")

    posts = topic.posts.select_related("author__profile").prefetch_related("images")
    first_post = posts.first()
    page = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get("page"))
    solution = None
    if topic.is_solved:
        solution = (Post.objects.select_related("author__profile").prefetch_related("images")
                    .filter(pk=topic.solution_id).first())
        if solution:
            solution.author_is_team = roles.can_moderate(solution.author)
    for post in page:
        post.author_is_team = roles.can_moderate(post.author)
        post.is_first = first_post is not None and post.pk == first_post.pk
    return render(request, "forum/topic.html", {
        "topic": topic, "page": page, "form": form, "solution": solution,
        "reply_count": max(topic.posts.count() - 1, 0),
        "can_reply": can_reply, "can_write": can_write, "can_moderate": can_moderate,
        "can_mark_solution": _can_mark_solution(request.user, topic),
    })


@login_required
@require_POST
def post_solution(request, pk):
    """Отметить ответ как решение вопроса (или снять отметку)."""
    post = get_object_or_404(Post.objects.select_related("topic__category"), pk=pk)
    topic = post.topic
    if not access.can_read(request.user, topic.category):
        raise Http404
    if not _can_mark_solution(request.user, topic) or topic.posts.first() == post:
        raise PermissionDenied
    if topic.solution_id == post.pk:
        topic.solution = None
        messages.info(request, _("Отметка «Решение» снята."))
    else:
        topic.solution = post
        messages.success(request, _("Ответ отмечен как решение."))
    topic.save(update_fields=["solution"])
    return redirect(f"{topic.get_absolute_url()}#post-{post.pk}")


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post.objects.select_related("topic__category", "topic__subforum"), pk=pk)
    if not access.can_read(request.user, post.topic.category):
        raise Http404
    if post.author != request.user and not roles.can_moderate(request.user):
        raise PermissionDenied
    topic = post.topic
    if topic.posts.first() == post:
        # Удаление первого сообщения удаляет всю публикацию
        subforum = topic.subforum
        topic.delete()
        messages.info(request, _("Публикация удалена."))
        return redirect(subforum)
    post.delete()
    messages.info(request, _("Сообщение удалено."))
    return redirect(topic)


@login_required
def post_image(request, pk, thumb=False):
    """Фото из сообщения — только тем, кто может читать эту главную тему.
    В продакшене файл отдаёт nginx (X-Accel-Redirect), Django лишь проверяет доступ."""
    image = get_object_or_404(PostImage.objects.select_related("post__topic__category"), pk=pk)
    if not access.can_read(request.user, image.post.topic.category):
        raise Http404
    field = image.thumb if thumb else image.image
    if settings.DOWNLOADS_ACCEL_PREFIX:
        response = HttpResponse(content_type="image/webp")
        response["X-Accel-Redirect"] = settings.DOWNLOADS_ACCEL_PREFIX.rstrip("/") + "/" + quote(field.name)
    else:
        try:
            response = FileResponse(field.open("rb"), content_type="image/webp")
        except FileNotFoundError:
            raise Http404
    response["Cache-Control"] = "private, max-age=86400"
    return response
