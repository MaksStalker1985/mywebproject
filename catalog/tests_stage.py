from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from accounts import roles
from django.contrib.auth.models import User

from .models import Product


def make(slug, stage=Product.Stage.RELEASE, **kw):
    data = dict(slug=slug, title=slug.title(), short_description="s", description="d", version="1.0",
                release_stage=stage)
    data.update(kw)
    return Product.objects.create(**data)


class StageCatalogTests(TestCase):
    def setUp(self):
        self.release = make("orbit", version="2.3.1")
        self.beta = make("city", Product.Stage.BETA, version="0.9-beta")
        self.alpha = make("nova", Product.Stage.ALPHA, version="0.1.0-alpha.2")

    def test_catalog_card_shows_version_and_stage_and_links_to_detail(self):
        page = self.client.get(reverse("catalog:list"))
        self.assertContains(page, "v2.3.1")
        self.assertContains(page, "Актуальная версия")
        self.assertContains(page, "Бета-тест")
        self.assertContains(page, "Альфа-тест")
        self.assertContains(page, 'href="%s"' % self.beta.get_absolute_url())
        with translation.override("en"):
            self.assertContains(self.client.get("/en/catalog/"), "Beta test")

    def test_filter_by_stage(self):
        page = self.client.get(reverse("catalog:list") + "?stage=alpha")
        self.assertEqual([p.slug for p in page.context["page"]], ["nova"])
        page = self.client.get(reverse("catalog:list") + "?stage=nonsense")
        self.assertEqual(len(page.context["page"]), 3)

    def test_detail_page_full_description(self):
        self.release.description = "Вступление\n\n## Возможности\n- Кооператив\n- <b>Моды</b>"
        self.release.changelog = "- Новый сектор"
        self.release.system_requirements = "- ОС: Windows 10"
        self.release.save()
        page = self.client.get(self.release.get_absolute_url())
        self.assertContains(page, "<h2>Возможности</h2>", html=False)
        self.assertContains(page, "<li>Кооператив</li>", html=False)
        self.assertNotContains(page, "<b>Моды</b>")  # HTML из описания экранируется
        self.assertContains(page, "Что нового в версии 2.3.1")
        self.assertContains(page, "ОС: Windows 10")
        self.assertContains(page, 'href="#requirements"')

    def test_detail_without_extra_sections_and_stage_notes(self):
        page = self.client.get(self.release.get_absolute_url())
        self.assertNotContains(page, 'id="changelog"')
        self.assertNotContains(page, "stage-note")
        self.assertContains(self.client.get(self.beta.get_absolute_url()), "stage-note-beta")
        self.assertContains(self.client.get(self.alpha.get_absolute_url()), "stage-note-alpha")

    def test_admin_sets_stage_in_dashboard(self):
        admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(admin, roles.ADMINS)
        self.client.force_login(admin)
        data = {"kind": "game", "title": "Orbit", "slug": "orbit", "genre": "", "short_description": "s",
                "description": "d", "developer": "", "version": "3.0-beta", "release_stage": "beta",
                "platform": "windows", "price": "0", "changelog": "- x", "system_requirements": "",
                "is_published": "on"}
        resp = self.client.post(reverse("dashboard:product_edit", args=[self.release.pk]), data)
        self.assertRedirects(resp, reverse("dashboard:products"))
        self.release.refresh_from_db()
        self.assertEqual((self.release.version, self.release.release_stage, self.release.changelog),
                         ("3.0-beta", "beta", "- x"))
