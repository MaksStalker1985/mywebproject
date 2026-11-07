from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.utils.translation import gettext as _

from catalog.models import Product
from forum import access as forum_access
from forum.models import Topic

from .forms import ContactForm
from .models import Page


def home(request):
    context = {
        "featured": Product.objects.filter(is_published=True, is_featured=True)[:6],
        "latest": Product.objects.filter(is_published=True)[:4],
        "games_count": Product.objects.filter(is_published=True, kind=Product.Kind.GAME).count(),
        "software_count": Product.objects.filter(is_published=True, kind=Product.Kind.SOFTWARE).count(),
        "topics": forum_access.visible_topics(request.user, Topic.objects.select_related("author__profile", "category"))[:5],
    }
    return render(request, "core/home.html", context)


def contact(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {"name": request.user.get_full_name() or request.user.username, "email": request.user.email}
    if "product" in request.GET:
        initial["product"] = request.GET["product"]

    form = ContactForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        # «Ответить» в почте сразу пишет посетителю
        EmailMessage(
            subject=f"[TechVault] {msg.get_topic_display()} — {msg.name}",
            body=f"{msg.message}\n\n{msg.name} <{msg.email}>\n{msg.product or ''}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[msg.email],
        ).send(fail_silently=True)
        messages.success(request, _("Спасибо! Ваше сообщение отправлено, мы ответим в ближайшее время."))
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form, "contact_email": settings.CONTACT_EMAIL})


def page(request, slug):
    """Информационная страница: условия, конфиденциальность, возвраты и т.п."""
    obj = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "core/page.html", {"page": obj})


@cache_page(60 * 60)
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /*/manage/",
        "Disallow: /*/admin/",
        "Disallow: /*/accounts/",
        "Disallow: /*/payments/",
        "Disallow: /payments/",
        "Disallow: /*/forum/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
