"""Заполняет базу демонстрационными данными: каталог, разделы форума, тестовые пользователи.

    python manage.py seed_demo
"""
import io
import zipfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts import roles
from catalog.models import Product
from forum.models import Category, Post, Topic

PRODUCTS = [
    dict(kind="game", slug="star-drift", title="Star Drift", genre="Космический симулятор", platform="windows",
         version="2.3.1", is_featured=True, developer="GameHub Studio", price=Decimal("349"),
         short_description="Исследуйте галактику, торгуйте и сражайтесь в открытом космосе.",
         description="Star Drift — космическая песочница с процедурно генерируемыми системами.\n\n"
                     "• Более 400 звёздных систем\n• Торговля и найм экипажа\n• Кооператив до 4 игроков"),
    dict(kind="game", slug="pixel-knights", title="Pixel Knights", genre="Платформер", platform="cross",
         version="1.0.4", is_featured=True, developer="GameHub Studio",
         short_description="Ретро-платформер с пиксельной графикой и боссами старой школы.",
         description="Пройдите 60 уровней в пяти мирах, собирайте снаряжение и победите Тёмного короля."),
    dict(kind="game", slug="city-architect", title="City Architect", genre="Стратегия", platform="windows",
         version="0.9-beta", developer="GameHub Studio", price=Decimal("199"),
         short_description="Градостроительный симулятор с реалистичной экономикой.",
         description="Стройте районы, прокладывайте транспорт и следите за счастьем жителей."),
    dict(kind="software", slug="hub-launcher", title="Hub Launcher", genre="Утилиты", platform="windows",
         version="4.1.0", is_featured=True, developer="GameHub",
         short_description="Лаунчер для установки и автообновления всех наших игр.",
         description="Hub Launcher автоматически скачивает обновления, проверяет целостность файлов "
                     "и синхронизирует сохранения в облаке."),
    dict(kind="software", slug="mod-studio", title="Mod Studio", genre="Разработка", platform="cross",
         version="1.6.2", developer="GameHub", price=Decimal("99.50"),
         short_description="Официальный редактор модификаций для Star Drift и City Architect.",
         description="Создавайте собственные карты, корабли и сценарии, публикуйте их для сообщества."),
    dict(kind="software", slug="frame-meter", title="Frame Meter", genre="Диагностика", platform="windows",
         version="2.0.0", is_featured=True, developer="GameHub",
         short_description="Лёгкий оверлей FPS и мониторинг загрузки CPU/GPU.",
         description="Показывает частоту кадров, время кадра и температуру компонентов поверх любой игры."),
    # Тестовая сборка: не опубликована, видна только тестерам и администраторам
    dict(kind="game", slug="star-drift-3-beta", title="Star Drift 3 (beta)", genre="Космический симулятор",
         platform="windows", version="3.0.0-beta.2", developer="GameHub Studio", price=Decimal("499"),
         is_published=False, for_testers=True,
         short_description="Закрытая бета третьей части: новые корабли и планетарные высадки.",
         description="Сборка для группы тестеров. Сообщайте о найденных ошибках в разделе форума "
                     "«Техническая поддержка»."),
]

CATEGORIES = [
    ("news", "Новости и анонсы", "Официальные новости команды"),
    ("games", "Обсуждение игр", "Впечатления, советы и прохождения"),
    ("support", "Техническая поддержка", "Проблемы с установкой и запуском"),
    ("mods", "Моды и инструменты", "Mod Studio, сборки и утилиты"),
]


def demo_archive(product):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("README.txt", f"{product['title']} {product['version']}\nДемо-файл GameHub.\n")
    return ContentFile(buf.getvalue(), name=f"{product['slug']}-{product['version']}.zip")


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные"

    @transaction.atomic
    def handle(self, *args, **options):
        for data in PRODUCTS:
            product, created = Product.objects.get_or_create(slug=data["slug"], defaults=data)
            if created:
                archive = demo_archive(data)
                product.file.save(archive.name, archive, save=True)

        for order, (slug, title, desc) in enumerate(CATEGORIES):
            Category.objects.get_or_create(slug=slug, defaults={"title": title, "description": desc, "order": order})

        admin, created = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@gamehub.local", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
        player, created = User.objects.get_or_create(username="player", defaults={"email": "player@gamehub.local"})
        if created:
            player.set_password("player12345")
            player.save()
        tester, created = User.objects.get_or_create(username="tester", defaults={"email": "tester@gamehub.local"})
        if created:
            tester.set_password("tester12345")
            tester.save()
        roles.set_role(admin, roles.ADMINS)
        roles.set_role(tester, roles.TESTERS)
        roles.set_role(player, roles.PLAYERS)

        if not Topic.objects.exists():
            news = Category.objects.get(slug="news")
            t = Topic.objects.create(category=news, author=admin, title="Добро пожаловать на форум GameHub!", is_pinned=True)
            Post.objects.create(topic=t, author=admin, body="Здесь вы можете обсуждать наши игры и программы, "
                                                             "задавать вопросы и делиться модами. Соблюдайте правила!")
            Post.objects.create(topic=t, author=player, body="Привет всем! Жду обновления Star Drift :)")

            support = Category.objects.get(slug="support")
            t = Topic.objects.create(category=support, author=player, title="Hub Launcher не видит установленные игры")
            Post.objects.create(topic=t, author=player, body="После переустановки Windows лаунчер показывает пустую библиотеку.")
            Post.objects.create(topic=t, author=admin, body="Нажмите «Библиотека → Найти установленные» и укажите папку с играми.")

        self.stdout.write(self.style.SUCCESS(
            "Демо-данные созданы. Пользователи: admin / admin12345 (администратор), "
            "tester / tester12345 (тестер), player / player12345 (игрок)."
        ))
