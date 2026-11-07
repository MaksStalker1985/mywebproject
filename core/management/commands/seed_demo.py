"""Заполняет базу демонстрационными данными: каталог, разделы форума, тестовые пользователи.

    python manage.py seed_demo
"""
import io
import zipfile
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts import roles
from catalog.models import Product
from forum.models import Category, Post, Subforum, Topic

PRODUCTS = [
    dict(kind="game", slug="star-drift", title="Star Drift", genre="Космический симулятор", platform="windows",
         version="2.3.1", is_featured=True, developer="TechVault Studio", price=Decimal("349"),
         short_description="Исследуйте галактику, торгуйте и сражайтесь в открытом космосе.",
         description="Star Drift — космическая песочница с процедурно генерируемыми системами.\n\n"
                     "- Более 400 звёздных систем\n- Торговля и найм экипажа\n- Кооператив до 4 игроков",
         changelog="- Новый сектор «Туманность Ориона»\n- Улучшен кооператив\n- Исправлены вылеты при прыжке",
         system_requirements="- ОС: Windows 10 64-bit\n- Процессор: 4 ядра, 3 ГГц\n- Память: 8 ГБ\n"
                             "- Видеокарта: GTX 1060 / RX 580\n- Место на диске: 12 ГБ"),
    dict(kind="game", slug="pixel-knights", title="Pixel Knights", genre="Платформер", platform="cross",
         version="1.0.4", is_featured=True, developer="TechVault Studio",
         short_description="Ретро-платформер с пиксельной графикой и боссами старой школы.",
         description="Пройдите 60 уровней в пяти мирах, собирайте снаряжение и победите Тёмного короля."),
    dict(kind="game", slug="city-architect", title="City Architect", genre="Стратегия", platform="windows",
         version="0.9-beta", release_stage="beta", developer="TechVault Studio", price=Decimal("199"),
         short_description="Градостроительный симулятор с реалистичной экономикой.",
         description="Стройте районы, прокладывайте транспорт и следите за счастьем жителей."),
    dict(kind="software", slug="hub-launcher", title="Hub Launcher", genre="Утилиты", platform="windows",
         version="4.1.0", is_featured=True, developer="TechVault",
         short_description="Лаунчер для установки и автообновления всех наших игр.",
         description="Hub Launcher автоматически скачивает обновления, проверяет целостность файлов "
                     "и синхронизирует сохранения в облаке."),
    dict(kind="software", slug="mod-studio", title="Mod Studio", genre="Разработка", platform="cross",
         version="1.6.2", developer="TechVault", price=Decimal("99.50"),
         short_description="Официальный редактор модификаций для Star Drift и City Architect.",
         description="Создавайте собственные карты, корабли и сценарии, публикуйте их для сообщества."),
    dict(kind="software", slug="frame-meter", title="Frame Meter", genre="Диагностика", platform="windows",
         version="2.0.0", is_featured=True, developer="TechVault",
         short_description="Лёгкий оверлей FPS и мониторинг загрузки CPU/GPU.",
         description="Показывает частоту кадров, время кадра и температуру компонентов поверх любой игры."),
    # Тестовая сборка: не опубликована, видна только тестерам и администраторам
    dict(kind="game", slug="star-drift-3-beta", title="Star Drift 3 (beta)", genre="Космический симулятор",
         platform="windows", version="3.0.0-beta.2", release_stage="beta", developer="TechVault Studio", price=Decimal("499"),
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

# Подтемы для каждой главной темы: (slug, название, описание)
SUBFORUMS = {
    "news": [("announcements", "Анонсы", "Новые игры, программы и даты выхода"),
             ("updates", "Обновления и патчи", "Что изменилось в новых версиях")],
    "games": [("star-drift", "Star Drift", "Исследование космоса, торговля, кооператив"),
              ("city-architect", "City Architect", "Градостроение и советы по планировке"),
              ("general", "Общее обсуждение", "Всё остальное об играх TechVault")],
    "support": [("install", "Установка и запуск", "Ошибки установки, вылеты, лаунчер"),
                ("payments", "Покупки и оплата", "Заказы, возвраты, доступ к загрузкам")],
    "mods": [("mod-studio", "Mod Studio", "Инструменты, API и документация"),
             ("showcase", "Готовые моды", "Делитесь своими сборками")],
}


def demo_archive(product):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("README.txt", f"{product['title']} {product['version']}\nДемо-файл TechVault.\n")
    return ContentFile(buf.getvalue(), name=f"{product['slug']}-{product['version']}.zip")


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Запустить при DJANGO_DEBUG=0 (создаёт пользователей с известными паролями!)")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("seed_demo создаёт пользователей с известными паролями и не запускается "
                               "при DJANGO_DEBUG=0. Для администратора используйте createsuperuser.")
        for data in PRODUCTS:
            product, created = Product.objects.get_or_create(slug=data["slug"], defaults=data)
            if created:
                archive = demo_archive(data)
                product.file.save(archive.name, archive, save=True)

        for order, (slug, title, desc) in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"title": title, "description": desc, "order": order})
            for sub_order, (sub_slug, sub_title, sub_desc) in enumerate(SUBFORUMS.get(slug, [])):
                Subforum.objects.get_or_create(category=cat, slug=sub_slug, defaults={
                    "title": sub_title, "description": sub_desc, "order": sub_order})

        admin, created = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@techvault.local", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
        player, created = User.objects.get_or_create(username="player", defaults={"email": "player@techvault.local"})
        if created:
            player.set_password("player12345")
            player.save()
        tester, created = User.objects.get_or_create(username="tester", defaults={"email": "tester@techvault.local"})
        if created:
            tester.set_password("tester12345")
            tester.save()
        roles.set_role(admin, roles.ADMINS)
        roles.set_role(tester, roles.TESTERS)
        roles.set_role(player, roles.PLAYERS)

        if not Topic.objects.exists():
            sub = lambda cat, slug: Subforum.objects.get(category__slug=cat, slug=slug)  # noqa: E731
            t = Topic.objects.create(subforum=sub("news", "announcements"), author=admin,
                                     title="Добро пожаловать на форум TechVault!", is_pinned=True)
            Post.objects.create(topic=t, author=admin, body="Здесь вы можете обсуждать наши игры и программы, "
                                                             "задавать вопросы и делиться модами. Соблюдайте правила!")
            Post.objects.create(topic=t, author=player, body="Привет всем! Жду обновления Star Drift :)")

            t = Topic.objects.create(subforum=sub("support", "install"), author=player, kind=Topic.Kind.QUESTION,
                                     title="Hub Launcher не видит установленные игры")
            Post.objects.create(topic=t, author=player, body="После переустановки Windows лаунчер показывает пустую библиотеку.")
            Post.objects.create(topic=t, author=tester, body="Попробуйте запустить лаунчер от имени администратора.")
            answer = Post.objects.create(topic=t, author=admin,
                                         body="Нажмите «Библиотека → Найти установленные» и укажите папку с играми.")
            Post.objects.create(topic=t, author=player, body="Помогло, спасибо!")
            t.solution = answer
            t.save(update_fields=["solution"])

            t = Topic.objects.create(subforum=sub("games", "star-drift"), author=tester, kind=Topic.Kind.QUESTION,
                                     title="Как открыть сектор «Туманность Ориона»?")
            Post.objects.create(topic=t, author=tester, body="Прошёл основную цепочку, но сектор на карте всё ещё закрыт.")

            t = Topic.objects.create(subforum=sub("games", "star-drift"), author=player,
                                     title="Лучшие маршруты для торговли в 2.0")
            Post.objects.create(topic=t, author=player, body="Делюсь своими маршрутами: Вега → Альтаир → Сириус приносит больше всего.")
            Post.objects.create(topic=t, author=tester, body="Добавлю: на Альтаире выгоднее брать редкие минералы.")

            t = Topic.objects.create(subforum=sub("news", "updates"), author=admin, title="Star Drift 2.0: что нового")
            Post.objects.create(topic=t, author=admin, body="Новый сектор, улучшенный кооператив и исправления вылетов.")

        self.stdout.write(self.style.SUCCESS(
            "Демо-данные созданы. Пользователи: admin / admin12345 (администратор), "
            "tester / tester12345 (тестер), player / player12345 (игрок)."
        ))
