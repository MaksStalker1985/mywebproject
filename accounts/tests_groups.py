from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Product
from forum.models import Category, CategoryAccess, Post, Topic

from . import roles
from .models import Role


def role_form_data(title, key="", levels=None, **perms):
    data = {"title": title, "key": key, "description": "", "color": "blue", "order": 20}
    data.update({k: "on" for k, v in perms.items() if v})
    for cat_id, level in (levels or {}).items():
        data[f"forum_{cat_id}"] = level
    return data


class GroupConfigTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(self.admin, roles.ADMINS)
        self.member = User.objects.create_user("member", "m@example.com", "S3cure-pass!")
        self.other = User.objects.create_user("other", "o@example.com", "S3cure-pass!")
        self.news = Category.objects.create(slug="news", title="News", order=0)
        self.secret = Category.objects.create(slug="secret", title="Secret", order=1)
        self.general = Category.objects.create(slug="general", title="General", order=2)
        self.secret_topic = Topic.objects.create(category=self.secret, author=self.admin, title="Hidden plans")
        Post.objects.create(topic=self.secret_topic, author=self.admin, body="x")
        self.news_topic = Topic.objects.create(category=self.news, author=self.admin, title="Release notes")
        Post.objects.create(topic=self.news_topic, author=self.admin, body="x")

    def _all_write(self):
        return {c.pk: "write" for c in Category.objects.all()}

    def _create_group(self, title, key, levels=None, **perms):
        self.client.force_login(self.admin)
        data = role_form_data(title, key, {**self._all_write(), **(levels or {})}, **perms)
        resp = self.client.post(reverse("dashboard:role_create"), data)
        self.assertRedirects(resp, reverse("dashboard:roles"))
        return Role.objects.get(group__name=key)

    def test_admin_creates_group_with_forum_access(self):
        role = self._create_group("Пресса", "press", {self.secret.pk: "none", self.news.pk: "read"},
                                  free_access_paid=True)
        self.assertTrue(role.free_access_paid)
        self.assertFalse(role.can_access_dashboard)
        self.assertEqual(dict(role.forum_access.values_list("category__slug", "level")),
                         {"secret": "none", "news": "read"})  # «write» не хранится

        roles.set_role(self.member, role)
        self.client.force_login(self.member)
        index = self.client.get(reverse("forum:index"))
        self.assertNotContains(index, "Secret")
        self.assertContains(index, "News")
        self.assertEqual(self.client.get(reverse("forum:category", args=["secret"])).status_code, 404)
        self.assertEqual(self.client.get(self.secret_topic.get_absolute_url()).status_code, 404)
        # Только чтение: тему видно, писать нельзя
        self.assertEqual(self.client.get(self.news_topic.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.post(self.news_topic.get_absolute_url(), {"body": "hi"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("forum:topic_create", args=["news"])).status_code, 403)
        # Полный доступ
        resp = self.client.post(reverse("forum:topic_create", args=["general"]), {"title": "Hello", "body": "Hi"})
        self.assertEqual(resp.status_code, 302)
        # Главная не показывает темы скрытого раздела
        self.assertNotContains(self.client.get(reverse("core:home")), "Hidden plans")

    def test_edit_group_permissions_and_forum(self):
        role = Role.objects.get(group__name=roles.TESTERS)
        roles.set_role(self.member, role)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 403)

        self.client.force_login(self.admin)
        data = role_form_data("Бета-тестеры", roles.TESTERS, {**self._all_write(), self.general.pk: "none"},
                              can_access_dashboard=True, can_see_test_builds=True)
        self.assertRedirects(self.client.post(reverse("dashboard:role_edit", args=[role.pk]), data),
                             reverse("dashboard:roles"))
        role.refresh_from_db()
        self.assertEqual((role.title, role.free_access_paid, role.can_access_dashboard), ("Бета-тестеры", False, True))
        self.assertTrue(User.objects.get(pk=self.member.pk).is_staff)

        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("forum:category", args=["general"])).status_code, 404)

        # Снова «полный доступ» — правило удаляется
        self.client.force_login(self.admin)
        data = role_form_data("Бета-тестеры", roles.TESTERS, self._all_write())
        self.client.post(reverse("dashboard:role_edit", args=[role.pk]), data)
        self.assertFalse(CategoryAccess.objects.filter(role=role).exists())
        self.assertFalse(User.objects.get(pk=self.member.pk).is_staff)

    def test_admins_group_keeps_dashboard_access(self):
        role = Role.objects.get(group__name=roles.ADMINS)
        self.client.force_login(self.admin)
        data = role_form_data("Админы", "renamed", self._all_write(), can_moderate_forum=True)
        self.client.post(reverse("dashboard:role_edit", args=[role.pk]), data)
        role.refresh_from_db()
        self.assertEqual((role.title, role.key, role.can_access_dashboard), ("Админы", roles.ADMINS, True))
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)

    def test_default_group_and_deletion(self):
        press = self._create_group("Пресса", "press", is_default=True)
        players = Role.objects.get(group__name=roles.PLAYERS)
        players.refresh_from_db()
        self.assertFalse(players.is_default)
        newbie = User.objects.create_user("newbie", "n@example.com", "S3cure-pass!")
        self.assertEqual(roles.get_role(newbie).key, "press")

        # Группу по умолчанию и администраторов удалить нельзя
        for role in (press, Role.objects.get(group__name=roles.ADMINS)):
            self.client.post(reverse("dashboard:role_delete", args=[role.pk]))
            self.assertTrue(Role.objects.filter(pk=role.pk).exists())

        testers = Role.objects.get(group__name=roles.TESTERS)
        roles.set_role(self.member, testers)
        self.assertEqual(self.client.get(reverse("dashboard:role_delete", args=[testers.pk])).status_code, 200)
        self.client.post(reverse("dashboard:role_delete", args=[testers.pk]))
        self.assertFalse(Group.objects.filter(name=roles.TESTERS).exists())
        self.assertEqual(roles.get_role(User.objects.get(pk=self.member.pk)).key, "press")

    def test_duplicate_key_rejected_and_non_admin_blocked(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("dashboard:role_create"), role_form_data("Copy", roles.TESTERS, self._all_write()))
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context["form"], "key", "Группа с таким ключом уже есть.")
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:roles")).status_code, 403)
        self.assertEqual(self.client.post(reverse("dashboard:role_create"),
                                          role_form_data("X", "x", can_access_dashboard=True)).status_code, 403)
        self.assertFalse(Group.objects.filter(name="x").exists())

    def test_moderator_group(self):
        mods = self._create_group("Модераторы", "mods", can_moderate_forum=True)
        roles.set_role(self.member, mods)
        topic = Topic.objects.create(category=self.general, author=self.other, title="T", is_locked=True)
        Post.objects.create(topic=topic, author=self.other, body="first")
        reply = Post.objects.create(topic=topic, author=self.other, body="second")

        self.client.force_login(self.member)
        self.assertEqual(self.client.post(topic.get_absolute_url(), {"body": "mod reply"}).status_code, 302)
        self.client.post(reverse("forum:post_delete", args=[reply.pk]))
        self.assertFalse(Post.objects.filter(pk=reply.pk).exists())
        # Обычный игрок не может ни того, ни другого
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(topic.get_absolute_url(), {"body": "no"}).status_code, 403)
        own = topic.posts.filter(author=self.member).first()
        self.assertEqual(self.client.post(reverse("forum:post_delete", args=[own.pk])).status_code, 403)


@override_settings(MEDIA_ROOT=__import__("tempfile").mkdtemp())
class CustomGroupCatalogTests(TestCase):
    def test_free_access_permission(self):
        group = Group.objects.create(name="vip")
        vip = Role.objects.create(group=group, title="VIP", free_access_paid=True)
        user = User.objects.create_user("vip", "v@example.com", "S3cure-pass!")
        p = Product.objects.create(slug="paid", title="Paid", short_description="s", description="d", price=Decimal("5"))
        p.file.save("p.zip", ContentFile(b"zip"))
        self.assertFalse(p.is_available_to(user))
        roles.set_role(user, vip)
        self.assertTrue(p.is_available_to(User.objects.get(pk=user.pk)))
