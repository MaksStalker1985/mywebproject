"""Стартовые юридические страницы. Тексты — шаблон: перед запуском продаж укажите реквизиты продавца
и проверьте условия с юристом (Панель управления → Страницы)."""
from django.db import migrations

SELLER_RU = "[Укажите продавца: ФИО ФОП или название компании, страну, адрес и регистрационный номер]"
SELLER_EN = "[Specify the seller: legal name of the company or sole proprietor, country, address and registration number]"
SELLER_UK = "[Вкажіть продавця: ПІБ ФОП або назву компанії, країну, адресу та реєстраційний номер]"

PAGES = [
    {
        "slug": "terms", "order": 1,
        "title_ru": "Условия использования", "title_en": "Terms of Service", "title_uk": "Умови використання",
        "body_ru": f"""Настоящие условия регулируют использование сайта TechVault (techvault.tech) и покупку цифровых продуктов — игр и программ.

## Продавец
{SELLER_RU}
Связь: support@techvault.tech

## Учётная запись
- Для форума и покупок нужна учётная запись. Вы отвечаете за сохранность пароля.
- Мы можем заблокировать учётную запись при нарушении этих условий или правил форума.

## Покупка и лицензия
- Цены указаны на странице продукта. Итоговая сумма с налогами показывается на странице оплаты.
- Оплата проводится через платёжного партнёра (Paddle или Stripe). Если оплата проходит через Paddle, продавцом по заказу выступает Paddle.com как официальный реселлер (Merchant of Record), и к оплате также применяются условия Paddle.
- После оплаты вы получаете личную непередаваемую лицензию на использование продукта. Купленные продукты доступны для скачивания в личном кабинете.
- Запрещено распространять, перепродавать и взламывать продукты.

## Форум
- Не публикуйте оскорбления, спам, незаконные материалы и чужие личные данные.
- Модераторы могут удалять сообщения и аватары, нарушающие правила.

## Ответственность
Продукты предоставляются «как есть». Перед покупкой проверьте системные требования на странице продукта. Мы не отвечаем за косвенные убытки, связанные с использованием продуктов, в пределах, допустимых законом.

## Изменения условий
Мы можем обновлять условия; актуальная версия всегда опубликована на этой странице.""",
        "body_en": f"""These terms govern the use of the TechVault website (techvault.tech) and the purchase of digital products — games and software.

## Seller
{SELLER_EN}
Contact: support@techvault.tech

## Account
- An account is required for the forum and purchases. You are responsible for keeping your password safe.
- We may suspend an account that violates these terms or the forum rules.

## Purchases and license
- Prices are shown on the product page. The final amount including taxes is shown at checkout.
- Payments are processed by our payment partner (Paddle or Stripe). When you pay via Paddle, Paddle.com is the Merchant of Record for your order and Paddle's buyer terms also apply.
- After payment you receive a personal, non-transferable license to use the product. Purchased products are available for download in your account.
- Redistributing, reselling or cracking products is prohibited.

## Forum
- Do not post insults, spam, illegal content or other people's personal data.
- Moderators may remove posts and avatars that break the rules.

## Liability
Products are provided "as is". Please check the system requirements on the product page before buying. To the extent permitted by law, we are not liable for indirect damages arising from the use of the products.

## Changes
We may update these terms; the current version is always published on this page.""",
        "body_uk": f"""Ці умови регулюють використання сайту TechVault (techvault.tech) і придбання цифрових продуктів — ігор і програм.

## Продавець
{SELLER_UK}
Зв'язок: support@techvault.tech

## Обліковий запис
- Для форуму та покупок потрібен обліковий запис. Ви відповідаєте за збереження пароля.
- Ми можемо заблокувати обліковий запис у разі порушення цих умов або правил форуму.

## Покупка і ліцензія
- Ціни вказано на сторінці продукту. Підсумкова сума з податками показується на сторінці оплати.
- Оплата проводиться через платіжного партнера (Paddle або Stripe). Якщо оплата проходить через Paddle, продавцем за замовленням виступає Paddle.com як офіційний реселер (Merchant of Record), і до оплати також застосовуються умови Paddle.
- Після оплати ви отримуєте особисту непередавану ліцензію на використання продукту. Придбані продукти доступні для завантаження в особистому кабінеті.
- Заборонено поширювати, перепродавати та зламувати продукти.

## Форум
- Не публікуйте образи, спам, незаконні матеріали та чужі персональні дані.
- Модератори можуть видаляти повідомлення та аватари, що порушують правила.

## Відповідальність
Продукти надаються «як є». Перед покупкою перевірте системні вимоги на сторінці продукту. Ми не відповідаємо за непрямі збитки, пов'язані з використанням продуктів, у межах, дозволених законом.

## Зміна умов
Ми можемо оновлювати умови; актуальна версія завжди опублікована на цій сторінці.""",
    },
    {
        "slug": "privacy", "order": 2,
        "title_ru": "Политика конфиденциальности", "title_en": "Privacy Policy", "title_uk": "Політика конфіденційності",
        "body_ru": f"""## Кто обрабатывает данные
{SELLER_RU}
Вопросы о данных: support@techvault.tech

## Какие данные мы собираем
- Учётная запись: логин, e-mail, пароль (хранится только в виде хэша), аватар.
- Покупки: состав заказа, сумма, статус и идентификатор платежа. Данные банковской карты вводятся на странице платёжного партнёра и к нам не попадают.
- Форум и обращения: ваши сообщения и данные из формы связи.
- Технические данные: IP-адрес и журналы сервера для безопасности.

## Зачем
Чтобы вести учётную запись, выдавать купленные продукты, отвечать на обращения, восстанавливать доступ по e-mail и защищать сайт от злоупотреблений.

## Кому передаём
- Платёжному партнёру (Paddle или Stripe) — для проведения оплаты.
- Почтовому сервису — для отправки писем.
Мы не продаём персональные данные.

## Cookie
Сайт использует только необходимые cookie: вход в учётную запись, защита форм (CSRF) и выбранный язык. Рекламных и аналитических cookie нет.

## Хранение и ваши права
Данные хранятся, пока существует учётная запись, а данные о покупках — столько, сколько требует закон. Вы можете запросить копию, исправление или удаление своих данных, написав на support@techvault.tech.""",
        "body_en": f"""## Who processes your data
{SELLER_EN}
Privacy questions: support@techvault.tech

## What we collect
- Account: username, e-mail, password (stored only as a hash), avatar.
- Purchases: order contents, amount, status and payment ID. Card details are entered on the payment partner's page and never reach us.
- Forum and messages: your posts and data from the contact form.
- Technical data: IP address and server logs for security.

## Why
To run your account, deliver purchased products, answer your requests, restore access by e-mail and protect the site from abuse.

## Who we share it with
- Our payment partner (Paddle or Stripe) — to process payments.
- Our e-mail provider — to send e-mails.
We do not sell personal data.

## Cookies
The site uses only essential cookies: login session, form protection (CSRF) and your language choice. There are no advertising or analytics cookies.

## Retention and your rights
Data is kept while your account exists; purchase records are kept as long as the law requires. You can request a copy, correction or deletion of your data by writing to support@techvault.tech.""",
        "body_uk": f"""## Хто обробляє дані
{SELLER_UK}
Питання щодо даних: support@techvault.tech

## Які дані ми збираємо
- Обліковий запис: логін, e-mail, пароль (зберігається лише у вигляді хешу), аватар.
- Покупки: склад замовлення, сума, статус та ідентифікатор платежу. Дані банківської картки вводяться на сторінці платіжного партнера й до нас не потрапляють.
- Форум і звернення: ваші повідомлення та дані з форми зв'язку.
- Технічні дані: IP-адреса та журнали сервера для безпеки.

## Навіщо
Щоб вести обліковий запис, видавати придбані продукти, відповідати на звернення, відновлювати доступ за e-mail і захищати сайт від зловживань.

## Кому передаємо
- Платіжному партнеру (Paddle або Stripe) — для проведення оплати.
- Поштовому сервісу — для надсилання листів.
Ми не продаємо персональні дані.

## Cookie
Сайт використовує лише необхідні cookie: вхід в обліковий запис, захист форм (CSRF) і обрану мову. Рекламних та аналітичних cookie немає.

## Зберігання і ваші права
Дані зберігаються, доки існує обліковий запис, а дані про покупки — стільки, скільки вимагає закон. Ви можете запросити копію, виправлення або видалення своїх даних, написавши на support@techvault.tech.""",
    },
    {
        "slug": "refunds", "order": 3,
        "title_ru": "Возврат средств", "title_en": "Refund Policy", "title_uk": "Повернення коштів",
        "body_ru": """## 14 дней на возврат
Если продукт не запускается на системе, соответствующей требованиям, или не соответствует описанию, напишите нам в течение 14 дней после покупки — мы вернём деньги.

## Как запросить возврат
- Напишите на support@techvault.tech или через форму «Связь с производителем».
- Укажите номер заказа (он есть в личном кабинете, раздел «История покупок») и причину.
- Возврат проводится тем же способом, которым была оплата. Сроки зачисления зависят от банка, обычно 5–10 рабочих дней.

## Если оплата проходила через Paddle
Возврат оформляет Paddle как продавец по заказу; вы также можете обратиться напрямую в поддержку Paddle по ссылке из письма о покупке.

После возврата доступ к скачиванию продукта закрывается.""",
        "body_en": """## 14-day refunds
If a product does not run on a system that meets the requirements, or does not match its description, contact us within 14 days of purchase and we will refund you.

## How to request a refund
- Write to support@techvault.tech or use the "Contact the developer" form.
- Include your order number (see "Purchase history" in your account) and the reason.
- Refunds go back to the original payment method. Processing time depends on your bank, usually 5–10 business days.

## Payments made via Paddle
Paddle, as the Merchant of Record, processes the refund; you can also contact Paddle support directly via the link in your purchase receipt.

After a refund, download access to the product is revoked.""",
        "body_uk": """## 14 днів на повернення
Якщо продукт не запускається на системі, що відповідає вимогам, або не відповідає опису, напишіть нам протягом 14 днів після покупки — ми повернемо гроші.

## Як запросити повернення
- Напишіть на support@techvault.tech або через форму «Зв'язок із виробником».
- Вкажіть номер замовлення (його видно в особистому кабінеті, розділ «Історія покупок») і причину.
- Повернення проводиться тим самим способом, яким була оплата. Строки зарахування залежать від банку, зазвичай 5–10 робочих днів.

## Якщо оплата проходила через Paddle
Повернення оформлює Paddle як продавець за замовленням; ви також можете звернутися безпосередньо до підтримки Paddle за посиланням із листа про покупку.

Після повернення доступ до завантаження продукту закривається.""",
    },
]


def create_pages(apps, schema_editor):
    Page = apps.get_model("core", "Page")
    for data in PAGES:
        Page.objects.get_or_create(slug=data["slug"], defaults=data)


def remove_pages(apps, schema_editor):
    apps.get_model("core", "Page").objects.filter(slug__in=[p["slug"] for p in PAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0002_page")]
    operations = [migrations.RunPython(create_pages, remove_pages)]
