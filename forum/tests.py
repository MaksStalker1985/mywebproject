from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts import roles

from .models import Category, Post, Subforum, Topic


class ForumStructureTests(TestCase):
    """Главная тема → подтема → публикация (обсуждение / вопрос с ответами)."""

    def setUp(self):
        self.cat = Category.objects.create(title="Поддержка", slug="support")
        self.install = Subforum.objects.create(category=self.cat, title="Установка", slug="install", order=0)
        self.pay = Subforum.objects.create(category=self.cat, title="Оплата", slug="payments", order=1)
        self.author = User.objects.create_user("asker", password="Pass-12345")
        self.helper = User.objects.create_user("helper", password="Pass-12345")
        self.mod = User.objects.create_user("mod", password="Pass-12345")
        roles.set_role(self.mod, roles.ADMINS)

    def _question(self):
        t = Topic.objects.create(subforum=self.install, author=self.author, kind=Topic.Kind.QUESTION, title="Не запускается")
        Post.objects.create(topic=t, author=self.author, body="Вопрос")
        answer = Post.objects.create(topic=t, author=self.helper, body="Ответ")
        return t, answer

    def test_index_and_category_show_subforums(self):
        self.client.force_login(self.author)
        index = self.client.get(reverse("forum:index"))
        self.assertContains(index, "Поддержка")
        self.assertContains(index, self.install.get_absolute_url())
        page = self.client.get(self.cat.get_absolute_url())
        self.assertContains(page, "Установка")
        self.assertContains(page, "Оплата")

    def test_create_question_in_subforum(self):
        self.client.force_login(self.author)
        url = reverse("forum:subforum_topic_create", args=["support", "payments"])
        resp = self.client.post(url, {"kind": "question", "title": "Где ключ?", "body": "Купил, но не вижу ключ"})
        topic = Topic.objects.get(title="Где ключ?")
        self.assertRedirects(resp, topic.get_absolute_url())
        self.assertEqual((topic.subforum, topic.category, topic.kind), (self.pay, self.cat, "question"))
        page = self.client.get(self.pay.get_absolute_url())
        self.assertContains(page, "Где ключ?")
        self.assertContains(page, "kind-question")
        self.assertNotContains(self.client.get(self.install.get_absolute_url()), "Где ключ?")

    def test_create_from_category_with_subforum_choice(self):
        self.client.force_login(self.author)
        self.client.post(reverse("forum:topic_create", args=["support"]),
                         {"subforum": self.pay.pk, "title": "Обсудим цены", "body": "..."})
        topic = Topic.objects.get(title="Обсудим цены")
        self.assertEqual((topic.subforum, topic.kind), (self.pay, "discussion"))

    def test_topic_without_subforum_goes_to_default(self):
        cat = Category.objects.create(title="Новая", slug="fresh")
        t = Topic.objects.create(category=cat, author=self.author, title="T")
        self.assertEqual((t.subforum.slug, t.subforum.category), ("general", cat))

    def test_author_marks_solution(self):
        topic, answer = self._question()
        self.client.force_login(self.helper)  # чужой вопрос — нельзя
        self.assertEqual(self.client.post(reverse("forum:post_solution", args=[answer.pk])).status_code, 403)
        self.client.force_login(self.author)
        self.client.post(reverse("forum:post_solution", args=[answer.pk]))
        topic.refresh_from_db()
        self.assertTrue(topic.is_solved)
        page = self.client.get(topic.get_absolute_url())
        self.assertContains(page, "Лучший ответ")
        self.assertContains(page, "post-solution")
        self.assertContains(self.client.get(self.install.get_absolute_url() + "?show=unsolved"), "Публикаций пока нет")
        # Повторное нажатие снимает отметку
        self.client.post(reverse("forum:post_solution", args=[answer.pk]))
        topic.refresh_from_db()
        self.assertFalse(topic.is_solved)

    def test_moderator_marks_solution_but_not_first_post(self):
        topic, answer = self._question()
        self.client.force_login(self.mod)
        first = topic.posts.first()
        self.assertEqual(self.client.post(reverse("forum:post_solution", args=[first.pk])).status_code, 403)
        self.client.post(reverse("forum:post_solution", args=[answer.pk]))
        topic.refresh_from_db()
        self.assertEqual(topic.solution, answer)

    def test_discussion_has_no_solution(self):
        t = Topic.objects.create(subforum=self.install, author=self.author, title="Болтаем")
        Post.objects.create(topic=t, author=self.author, body="1")
        reply = Post.objects.create(topic=t, author=self.helper, body="2")
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(reverse("forum:post_solution", args=[reply.pk])).status_code, 403)
        self.assertNotContains(self.client.get(t.get_absolute_url()), "Это решение")

    def test_deleting_solution_post_clears_it(self):
        topic, answer = self._question()
        topic.solution = answer
        topic.save()
        answer.delete()
        topic.refresh_from_db()
        self.assertIsNone(topic.solution)

    def test_subforum_access_follows_category(self):
        from forum.models import CategoryAccess
        CategoryAccess.objects.create(category=self.cat, role=roles.get_role(self.author), level="none")
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(self.install.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(reverse("forum:subforum_topic_create", args=["support", "install"])).status_code, 404)

    def test_dashboard_manages_subforums(self):
        self.client.force_login(self.mod)
        resp = self.client.post(reverse("dashboard:subforum_create"),
                                {"category": self.cat.pk, "title": "Вылеты", "slug": "crashes", "description": "", "order": 3})
        self.assertRedirects(resp, reverse("dashboard:categories"))
        self.assertTrue(Subforum.objects.filter(category=self.cat, slug="crashes").exists())
        # Адрес «new» и повтор адреса в той же главной теме запрещены
        for slug in ["new", "install"]:
            resp = self.client.post(reverse("dashboard:subforum_create"),
                                    {"category": self.cat.pk, "title": "X", "slug": slug, "description": "", "order": 0})
            self.assertEqual(resp.status_code, 200)
        self.assertContains(self.client.get(reverse("dashboard:categories")), "Вылеты")


class ThemeTests(TestCase):
    def test_base_has_theme_toggle_and_both_logos(self):
        page = self.client.get(reverse("core:home"))
        self.assertContains(page, 'id="theme-toggle"')
        self.assertContains(page, "logo-header-light.webp")
        self.assertContains(page, "logo-header-dark.webp")
        self.assertContains(page, 'data-theme="dark"')
