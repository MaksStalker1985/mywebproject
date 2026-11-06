import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product
from payments.models import Order

from . import roles

MEDIA = tempfile.mkdtemp()


def content(resp):
    return b"".join(resp.streaming_content)


@override_settings(MEDIA_ROOT=MEDIA)
class RoleTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.player = User.objects.create_user("player", "p@example.com", "S3cure-pass!")
        self.tester = User.objects.create_user("tester", "t@example.com", "S3cure-pass!")
        roles.set_role(self.tester, roles.TESTERS)
        self.paid = Product.objects.create(slug="paid", title="Paid", short_description="s", description="d",
                                           price=Decimal("100"))
        self.paid.file.save("paid.zip", ContentFile(b"paid"))
        self.beta = Product.objects.create(slug="beta", title="Beta", short_description="s", description="d",
                                           price=Decimal("50"), is_published=False, for_testers=True)
        self.beta.file.save("beta.zip", ContentFile(b"beta"))
        self.draft = Product.objects.create(slug="draft", title="Draft", short_description="s", description="d",
                                            is_published=False)

    def test_groups_exist_and_new_user_is_player(self):
        self.assertTrue({roles.ADMINS, roles.TESTERS, roles.PLAYERS} <= set(Group.objects.values_list("name", flat=True)))
        self.assertEqual(roles.get_role(self.player).key, roles.PLAYERS)
        admin = User.objects.create_superuser("root", "r@example.com", "S3cure-pass!")
        self.assertEqual(roles.get_role(admin).key, roles.ADMINS)
        self.assertTrue(admin.groups.filter(name=roles.ADMINS).exists())

    def test_set_role_syncs_staff_flag(self):
        roles.set_role(self.player, roles.ADMINS)
        self.assertTrue(self.player.is_staff)
        self.assertEqual(list(self.player.groups.values_list("name", flat=True)), [roles.ADMINS])
        roles.set_role(self.player, roles.PLAYERS)
        self.assertFalse(User.objects.get(pk=self.player.pk).is_staff)
        # Как в Django admin: добавление в группу с другой стороны связи
        Group.objects.get(name=roles.ADMINS).user_set.add(self.player)
        self.assertTrue(User.objects.get(pk=self.player.pk).is_staff)

    def test_tester_gets_paid_products_and_test_builds(self):
        self.client.force_login(self.tester)
        self.assertEqual(content(self.client.get(reverse("catalog:download", args=["paid"]))), b"paid")
        self.assertEqual(self.client.get(reverse("catalog:detail", args=["beta"])).status_code, 200)
        self.assertEqual(content(self.client.get(reverse("catalog:download", args=["beta"]))), b"beta")
        # Обычный черновик тестеру не виден
        self.assertEqual(self.client.get(reverse("catalog:detail", args=["draft"])).status_code, 404)
        # Тестовая сборка не попадает в публичный каталог
        self.assertNotContains(self.client.get(reverse("catalog:list")), "Beta")
        cabinet = self.client.get(reverse("accounts:cabinet"))
        self.assertContains(cabinet, "Beta")
        self.assertContains(cabinet, reverse("catalog:download", args=["paid"]))

    def test_player_cannot_see_test_build_or_download_paid(self):
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(reverse("catalog:detail", args=["beta"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("catalog:download", args=["beta"])).status_code, 404)
        self.assertRedirects(self.client.get(reverse("catalog:download", args=["paid"])), self.paid.get_absolute_url())
        self.assertNotContains(self.client.get(reverse("accounts:cabinet")), reverse("catalog:download", args=["paid"]))

    def test_cabinet_library_and_history(self):
        Order.objects.create(user=self.player, product=self.paid, amount=Decimal("100"), currency="UAH",
                             provider="demo", status=Order.Status.PAID, paid_at=timezone.now())
        Order.objects.create(user=self.player, product=self.beta, amount=Decimal("50"), currency="UAH",
                             provider="demo", status=Order.Status.CANCELLED)
        other = User.objects.create_user("other", "o@example.com", "S3cure-pass!")
        Order.objects.create(user=other, product=self.paid, amount=Decimal("1"), currency="UAH", provider="demo")

        self.assertIn(reverse("accounts:login"), self.client.get(reverse("accounts:cabinet")).url)
        self.client.force_login(self.player)
        cabinet = self.client.get(reverse("accounts:cabinet"))
        self.assertEqual([p.slug for p in cabinet.context["library"]], ["paid"])
        self.assertContains(cabinet, reverse("catalog:download", args=["paid"]))
        self.assertEqual(cabinet.context["stats"]["spent"], [{"currency": "UAH", "total": Decimal("100")}])

        history = self.client.get(reverse("accounts:orders"))
        self.assertEqual(len(history.context["page"]), 2)  # чужой заказ не виден
        paid_only = self.client.get(reverse("accounts:orders") + "?status=paid")
        self.assertEqual([o.product.slug for o in paid_only.context["page"]], ["paid"])
        # Старый адрес «Мои покупки» ведёт в кабинет
        self.assertRedirects(self.client.get(reverse("payments:orders")), reverse("accounts:orders"))

    def test_purchased_product_stays_downloadable_after_unpublish(self):
        Order.objects.create(user=self.player, product=self.paid, amount=Decimal("100"), currency="UAH",
                             provider="demo", status=Order.Status.PAID, paid_at=timezone.now())
        Product.objects.filter(pk=self.paid.pk).update(is_published=False)
        self.client.force_login(self.player)
        self.assertEqual(content(self.client.get(reverse("catalog:download", args=["paid"]))), b"paid")


class RoleManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("boss", "b@example.com", "S3cure-pass!")
        roles.set_role(self.admin, roles.ADMINS)
        self.player = User.objects.create_user("player", "p@example.com", "S3cure-pass!")
        self.tester = User.objects.create_user("tester", "t@example.com", "S3cure-pass!")
        roles.set_role(self.tester, roles.TESTERS)

    def test_only_admins_manage_roles(self):
        url = reverse("dashboard:user_role", args=[self.player.pk])
        self.client.force_login(self.tester)
        self.assertEqual(self.client.get(reverse("dashboard:users")).status_code, 403)
        self.assertEqual(self.client.post(url, {"role": roles.ADMINS}).status_code, 403)
        self.assertEqual(roles.get_role(User.objects.get(pk=self.player.pk)).key, roles.PLAYERS)

    def test_admin_changes_role(self):
        self.client.force_login(self.admin)
        page = self.client.get(reverse("dashboard:users") + "?role=testers")
        self.assertEqual([u.username for u in page.context["page_obj"]], ["tester"])
        self.client.post(reverse("dashboard:user_role", args=[self.player.pk]), {"role": roles.TESTERS})
        self.assertEqual(roles.get_role(User.objects.get(pk=self.player.pk)).key, roles.TESTERS)
        # Себя понизить нельзя, неизвестная роль отклоняется
        self.client.post(reverse("dashboard:user_role", args=[self.admin.pk]), {"role": roles.PLAYERS})
        self.client.post(reverse("dashboard:user_role", args=[self.player.pk]), {"role": "gods"})
        self.assertEqual(roles.get_role(User.objects.get(pk=self.admin.pk)).key, roles.ADMINS)
        self.assertEqual(roles.get_role(User.objects.get(pk=self.player.pk)).key, roles.TESTERS)

    def test_new_admin_gets_dashboard(self):
        roles.set_role(self.player, roles.ADMINS)
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)
        roles.set_role(self.player, roles.PLAYERS)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 403)
