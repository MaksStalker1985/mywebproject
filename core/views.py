from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from catalog.models import Product
from forum import access as forum_access
from forum.models import Topic

from .forms import ContactForm


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
        send_mail(
            subject=f"[GameHub] {msg.get_topic_display()} — {msg.name}",
            message=f"{msg.message}\n\n{msg.name} <{msg.email}>\n{msg.product or ''}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=True,
        )
        messages.success(request, _("Спасибо! Ваше сообщение отправлено, мы ответим в ближайшее время."))
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form, "contact_email": settings.CONTACT_EMAIL})
