from django.conf import settings

from .models import Page


def site(request):
    """Ссылки на информационные страницы в подвале и контакт поддержки."""
    return {
        "footer_pages": Page.objects.filter(is_published=True, show_in_footer=True).only(
            "slug", "title_ru", "title_en", "title_uk"),
        "support_email": settings.CONTACT_EMAIL,
    }
