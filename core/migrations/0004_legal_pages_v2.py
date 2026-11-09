"""Юридические страницы из документов владельца (Terms of Service, Privacy Policy, Refund Policy,
редакция от 9 ноября 2026). Английский текст — оригинал, русский и украинский — переводы.
Тексты можно править в Панели управления → Страницы."""
from django.db import migrations

ADDRESS_EN = "Zhitomirskaya str. 164, Odesa, Ukraine, 65085"
ADDRESS_RU = "ул. Житомирская, 164, Одесса, Украина, 65085"
ADDRESS_UK = "вул. Житомирська, 164, Одеса, Україна, 65085"

# --------------------------------------------------------------------------- Terms of Service
TERMS_EN = f"""Effective Date: November 9, 2026

Welcome to techvault ("techvault", "we", "us", or "our"), operated by Maksym Rozhdestvenskyi, an independent software developer based in Ukraine.

Website: https://techvault.tech
General Contact: office@techvault.tech
Technical Support: support@techvault.tech
Refunds: refund@techvault.tech

These Terms of Service govern your access to and use of our website, software, games, digital products, user accounts, and related services.

By accessing our services or purchasing our products, you agree to these Terms. If you do not agree, please do not use our services.

## 1. Scope of Services
techvault develops, publishes, licenses, and distributes software applications, games, utilities, and other digital products.

Products may be provided as free software, paid software, trial versions, beta releases, Early Access versions, subscription services, or other distribution models.

Specific products may be governed by additional End User License Agreements (EULAs) or product-specific terms.

## 2. Eligibility and Accounts
You must have the legal capacity to enter into a binding agreement under applicable law.

If you are below the age of legal majority in your jurisdiction, you must obtain permission from your parent or legal guardian.

When creating an account, you agree to provide accurate information, protect your credentials, and notify us of suspected unauthorized access.

You are responsible for activity performed through your account, except where applicable law provides otherwise.

## 3. Software Licensing
Unless expressly stated otherwise in a product-specific license agreement, purchasing a software product grants you a limited, non-exclusive, non-transferable license to use the software for its intended purposes.

The license may be personal or commercial depending on the product and its published licensing conditions.

Purchasing a license does not transfer ownership of the software, source code, trademarks, or other intellectual property.

Unless expressly permitted by the applicable license or mandatory law, you may not:
- Redistribute, sublicense, or resell software licenses.
- Circumvent licensing or security systems.
- Reverse engineer protected software components.
- Distribute unauthorized copies.
- Use our products for unlawful purposes.

## 4. Software Activation and Account-Based Licensing
Certain products may require account registration, online activation, license keys, or periodic license verification.

Device limits, activation procedures, offline access availability, and license transfer rules may vary between products.

Specific licensing requirements will be disclosed in the applicable product description or license agreement.

## 5. Purchases and Payments
Product prices, currencies, applicable taxes, and available payment methods will be displayed during checkout.

Payments may be processed through authorized third-party payment providers.

The seller or merchant of record will be identified where required.

Refunds are governed by our Refund Policy and applicable consumer protection laws.

Refund Policy: https://www.techvault.tech/refund-policy

## 6. Early Access, Beta, and Trial Software
Some products may be distributed before their final release.

Such products may contain incomplete features, software bugs, compatibility issues, and other limitations.

Development plans, release dates, and features may change unless otherwise contractually guaranteed.

Early Access or beta designation does not exclude mandatory statutory consumer rights.

## 7. Software Updates and Availability
We may release software updates, security patches, bug fixes, or additional features.

Some updates may be necessary for security, compatibility, or continued use of online services.

We do not guarantee uninterrupted availability of online services, subject to applicable law and contractual obligations.

## 8. Intellectual Property
All software, source code, artwork, documentation, branding, and related content remain the intellectual property of techvault or their respective owners.

Unauthorized reproduction, distribution, or commercial exploitation is prohibited except as permitted by law or license.

## 9. User Content and Community Services
Users are responsible for content submitted to forums, reviews, or other interactive services.

Users must not submit unlawful, malicious, infringing, or abusive content.

We may moderate content and restrict access where reasonably necessary, subject to applicable law.

## 10. Suspension and Termination
We may restrict or suspend access due to fraud, unauthorized use, serious security concerns, or violations of these Terms.

Any termination will respect applicable statutory rights and existing contractual entitlements.

## 11. Disclaimer and Limitation of Liability
Products and services are provided subject to the warranties and consumer protections required by applicable law.

To the maximum extent permitted by law, techvault is not liable for indirect or consequential losses.

Nothing in these Terms excludes liability or consumer rights that cannot lawfully be excluded.

## 12. Privacy
Personal data is processed in accordance with our Privacy Policy:
https://www.techvault.tech/privacy-policy

## 13. Refunds
Refund requests are handled under our Refund Policy:
https://www.techvault.tech/refund-policy

Refund inquiries: refund@techvault.tech

## 14. Governing Law
These Terms are governed by the laws of Ukraine, except where mandatory consumer protection rules or applicable conflict-of-law provisions require otherwise.

## 15. Changes to These Terms
We may update these Terms when necessary.

Material changes affecting existing rights will be communicated where required by law.

## 16. Contact Information
Developer: Maksym Rozhdestvenskyi (techvault)
Country: Ukraine
Website: https://www.techvault.tech
General and Legal Inquiries: office@techvault.tech
Technical Support: support@techvault.tech
Refunds and Billing Disputes: refund@techvault.tech
Legal correspondence address: {ADDRESS_EN}"""

TERMS_RU = f"""Дата вступления в силу: 9 ноября 2026 г.

Добро пожаловать в techvault («techvault», «мы», «нас» или «наш»). Сервис управляется Максимом Рождественским — независимым разработчиком программного обеспечения из Украины.

Сайт: https://techvault.tech
Общие вопросы: office@techvault.tech
Техническая поддержка: support@techvault.tech
Возвраты: refund@techvault.tech

Настоящие Условия использования регулируют доступ к нашему сайту, программному обеспечению, играм, цифровым продуктам, учётным записям пользователей и связанным сервисам, а также их использование.

Получая доступ к нашим сервисам или покупая наши продукты, вы соглашаетесь с настоящими Условиями. Если вы не согласны с ними, пожалуйста, не пользуйтесь нашими сервисами.

## 1. Сфера услуг
techvault разрабатывает, издаёт, лицензирует и распространяет программы, игры, утилиты и другие цифровые продукты.

Продукты могут предоставляться как бесплатное или платное программное обеспечение, пробные версии, бета-версии, версии раннего доступа (Early Access), подписки или по иным моделям распространения.

На отдельные продукты могут распространяться дополнительные лицензионные соглашения с конечным пользователем (EULA) или условия конкретного продукта.

## 2. Право пользования и учётные записи
Вы должны обладать дееспособностью, достаточной для заключения обязывающего договора в соответствии с применимым законодательством.

Если вы не достигли совершеннолетия в своей юрисдикции, вам необходимо разрешение родителя или законного представителя.

Создавая учётную запись, вы обязуетесь указывать достоверные данные, обеспечивать сохранность своих учётных данных и сообщать нам о подозрении на несанкционированный доступ.

Вы несёте ответственность за действия, совершённые через вашу учётную запись, если применимое законодательство не предусматривает иное.

## 3. Лицензирование программного обеспечения
Если в лицензионном соглашении конкретного продукта прямо не указано иное, покупка программного продукта предоставляет вам ограниченную, неисключительную, непередаваемую лицензию на использование программы по её назначению.

Лицензия может быть личной или коммерческой — в зависимости от продукта и опубликованных условий его лицензирования.

Покупка лицензии не передаёт вам право собственности на программное обеспечение, исходный код, товарные знаки или иную интеллектуальную собственность.

Если иное прямо не разрешено применимой лицензией или императивными нормами закона, запрещается:
- Распространять, сублицензировать или перепродавать лицензии на программное обеспечение.
- Обходить системы лицензирования или защиты.
- Выполнять обратную разработку (reverse engineering) защищённых компонентов программ.
- Распространять несанкционированные копии.
- Использовать наши продукты в незаконных целях.

## 4. Активация программ и лицензирование через учётную запись
Для некоторых продуктов может потребоваться регистрация учётной записи, онлайн-активация, лицензионные ключи или периодическая проверка лицензии.

Ограничения по количеству устройств, порядок активации, возможность работы без подключения к сети и правила передачи лицензии могут различаться для разных продуктов.

Конкретные требования к лицензированию указываются в описании продукта или в соответствующем лицензионном соглашении.

## 5. Покупки и платежи
Цены продуктов, валюты, применимые налоги и доступные способы оплаты отображаются при оформлении заказа.

Платежи могут обрабатываться уполномоченными сторонними платёжными провайдерами.

Продавец или официальный реселлер (Merchant of Record) указывается в случаях, когда это требуется.

Возвраты регулируются нашими Правилами возврата и применимым законодательством о защите прав потребителей.

Правила возврата: https://www.techvault.tech/refund-policy

## 6. Ранний доступ, бета- и пробные версии
Некоторые продукты могут распространяться до выхода финальной версии.

Такие продукты могут содержать незавершённые функции, программные ошибки, проблемы совместимости и другие ограничения.

Планы разработки, даты выхода и функции могут меняться, если иное не гарантировано договором.

Статус раннего доступа или бета-версии не исключает обязательных прав потребителя, предусмотренных законом.

## 7. Обновления и доступность программ
Мы можем выпускать обновления программ, исправления безопасности, исправления ошибок и новые функции.

Некоторые обновления могут быть необходимы для безопасности, совместимости или дальнейшего использования онлайн-сервисов.

Мы не гарантируем бесперебойную работу онлайн-сервисов, с учётом применимого законодательства и договорных обязательств.

## 8. Интеллектуальная собственность
Всё программное обеспечение, исходный код, графика, документация, элементы бренда и связанные материалы остаются интеллектуальной собственностью techvault или соответствующих правообладателей.

Несанкционированное воспроизведение, распространение или коммерческое использование запрещено, кроме случаев, разрешённых законом или лицензией.

## 9. Пользовательский контент и сообщество
Пользователи несут ответственность за материалы, публикуемые на форуме, в отзывах и других интерактивных сервисах.

Запрещается публиковать незаконные, вредоносные, нарушающие чужие права или оскорбительные материалы.

Мы можем модерировать контент и ограничивать доступ, когда это обоснованно необходимо, с учётом применимого законодательства.

## 10. Приостановка и прекращение доступа
Мы можем ограничить или приостановить доступ в случае мошенничества, несанкционированного использования, серьёзных угроз безопасности или нарушения настоящих Условий.

Любое прекращение доступа осуществляется с соблюдением прав, предусмотренных законом, и действующих договорных обязательств.

## 11. Отказ от гарантий и ограничение ответственности
Продукты и услуги предоставляются с гарантиями и мерами защиты потребителей, которые требуются применимым законодательством.

В максимальной степени, допустимой законом, techvault не несёт ответственности за косвенные или последующие убытки.

Ничто в настоящих Условиях не исключает ответственность или права потребителей, которые не могут быть исключены по закону.

## 12. Конфиденциальность
Персональные данные обрабатываются в соответствии с нашей Политикой конфиденциальности:
https://www.techvault.tech/privacy-policy

## 13. Возвраты
Запросы на возврат рассматриваются в соответствии с нашими Правилами возврата:
https://www.techvault.tech/refund-policy

Вопросы о возвратах: refund@techvault.tech

## 14. Применимое право
Настоящие Условия регулируются законодательством Украины, за исключением случаев, когда императивные нормы о защите прав потребителей или применимые коллизионные нормы требуют иного.

## 15. Изменение Условий
Мы можем обновлять настоящие Условия по мере необходимости.

О существенных изменениях, затрагивающих уже имеющиеся права, мы сообщим, если этого требует закон.

## 16. Контактная информация
Разработчик: Максим Рождественский (techvault)
Страна: Украина
Сайт: https://www.techvault.tech
Общие и юридические вопросы: office@techvault.tech
Техническая поддержка: support@techvault.tech
Возвраты и платёжные споры: refund@techvault.tech
Адрес для юридической корреспонденции: {ADDRESS_RU}

Переводы на русский и украинский языки приведены для удобства; при расхождении преимущество имеет английская версия."""

TERMS_UK = f"""Дата набрання чинності: 9 листопада 2026 р.

Ласкаво просимо до techvault («techvault», «ми», «нас» або «наш»). Сервісом керує Максим Рождественський — незалежний розробник програмного забезпечення з України.

Сайт: https://techvault.tech
Загальні питання: office@techvault.tech
Технічна підтримка: support@techvault.tech
Повернення коштів: refund@techvault.tech

Ці Умови використання регулюють доступ до нашого сайту, програмного забезпечення, ігор, цифрових продуктів, облікових записів користувачів і пов'язаних сервісів, а також їх використання.

Отримуючи доступ до наших сервісів або купуючи наші продукти, ви погоджуєтеся з цими Умовами. Якщо ви не згодні з ними, будь ласка, не користуйтеся нашими сервісами.

## 1. Сфера послуг
techvault розробляє, видає, ліцензує та поширює програми, ігри, утиліти та інші цифрові продукти.

Продукти можуть надаватися як безкоштовне або платне програмне забезпечення, пробні версії, бета-версії, версії раннього доступу (Early Access), підписки або за іншими моделями поширення.

На окремі продукти можуть поширюватися додаткові ліцензійні угоди з кінцевим користувачем (EULA) або умови конкретного продукту.

## 2. Право користування та облікові записи
Ви повинні мати дієздатність, достатню для укладення обов'язкового договору відповідно до застосовного законодавства.

Якщо ви не досягли повноліття у своїй юрисдикції, вам потрібен дозвіл батьків або законного представника.

Створюючи обліковий запис, ви зобов'язуєтеся вказувати достовірні дані, забезпечувати збереження своїх облікових даних і повідомляти нас про підозру на несанкціонований доступ.

Ви несете відповідальність за дії, вчинені через ваш обліковий запис, якщо застосовне законодавство не передбачає іншого.

## 3. Ліцензування програмного забезпечення
Якщо в ліцензійній угоді конкретного продукту прямо не зазначено інше, купівля програмного продукту надає вам обмежену, невиключну ліцензію без права передачі на використання програми за її призначенням.

Ліцензія може бути особистою або комерційною — залежно від продукту та опублікованих умов його ліцензування.

Купівля ліцензії не передає вам права власності на програмне забезпечення, вихідний код, торговельні марки чи іншу інтелектуальну власність.

Якщо інше прямо не дозволено застосовною ліцензією або імперативними нормами закону, забороняється:
- Поширювати, субліцензувати або перепродавати ліцензії на програмне забезпечення.
- Обходити системи ліцензування чи захисту.
- Здійснювати зворотну розробку (reverse engineering) захищених компонентів програм.
- Поширювати несанкціоновані копії.
- Використовувати наші продукти з незаконною метою.

## 4. Активація програм і ліцензування через обліковий запис
Для деяких продуктів може знадобитися реєстрація облікового запису, онлайн-активація, ліцензійні ключі або періодична перевірка ліцензії.

Обмеження кількості пристроїв, порядок активації, можливість роботи без підключення до мережі та правила передачі ліцензії можуть відрізнятися для різних продуктів.

Конкретні вимоги до ліцензування зазначаються в описі продукту або у відповідній ліцензійній угоді.

## 5. Покупки та платежі
Ціни продуктів, валюти, застосовні податки та доступні способи оплати відображаються під час оформлення замовлення.

Платежі можуть оброблятися уповноваженими сторонніми платіжними провайдерами.

Продавець або офіційний реселер (Merchant of Record) зазначається у випадках, коли це потрібно.

Повернення коштів регулюються нашими Правилами повернення та застосовним законодавством про захист прав споживачів.

Правила повернення: https://www.techvault.tech/refund-policy

## 6. Ранній доступ, бета- та пробні версії
Деякі продукти можуть поширюватися до виходу фінальної версії.

Такі продукти можуть містити незавершені функції, програмні помилки, проблеми сумісності та інші обмеження.

Плани розробки, дати виходу та функції можуть змінюватися, якщо інше не гарантовано договором.

Статус раннього доступу чи бета-версії не виключає обов'язкових прав споживача, передбачених законом.

## 7. Оновлення та доступність програм
Ми можемо випускати оновлення програм, виправлення безпеки, виправлення помилок і нові функції.

Деякі оновлення можуть бути необхідними для безпеки, сумісності або подальшого використання онлайн-сервісів.

Ми не гарантуємо безперебійної роботи онлайн-сервісів з урахуванням застосовного законодавства та договірних зобов'язань.

## 8. Інтелектуальна власність
Усе програмне забезпечення, вихідний код, графіка, документація, елементи бренду та пов'язані матеріали залишаються інтелектуальною власністю techvault або відповідних правовласників.

Несанкціоноване відтворення, поширення чи комерційне використання заборонено, крім випадків, дозволених законом або ліцензією.

## 9. Користувацький контент і спільнота
Користувачі несуть відповідальність за матеріали, які публікують на форумі, у відгуках та інших інтерактивних сервісах.

Забороняється публікувати незаконні, шкідливі, такі, що порушують чужі права, або образливі матеріали.

Ми можемо модерувати контент і обмежувати доступ, коли це обґрунтовано необхідно, з урахуванням застосовного законодавства.

## 10. Призупинення та припинення доступу
Ми можемо обмежити або призупинити доступ у разі шахрайства, несанкціонованого використання, серйозних загроз безпеці або порушення цих Умов.

Будь-яке припинення доступу здійснюється з дотриманням прав, передбачених законом, і чинних договірних зобов'язань.

## 11. Відмова від гарантій і обмеження відповідальності
Продукти та послуги надаються з гарантіями та заходами захисту споживачів, яких вимагає застосовне законодавство.

У максимальному обсязі, дозволеному законом, techvault не несе відповідальності за непрямі або подальші збитки.

Ніщо в цих Умовах не виключає відповідальності чи прав споживачів, які не можуть бути виключені згідно із законом.

## 12. Конфіденційність
Персональні дані обробляються відповідно до нашої Політики конфіденційності:
https://www.techvault.tech/privacy-policy

## 13. Повернення коштів
Запити на повернення розглядаються відповідно до наших Правил повернення:
https://www.techvault.tech/refund-policy

Питання щодо повернень: refund@techvault.tech

## 14. Застосовне право
Ці Умови регулюються законодавством України, крім випадків, коли імперативні норми про захист прав споживачів або застосовні колізійні норми вимагають іншого.

## 15. Зміна Умов
Ми можемо оновлювати ці Умови за потреби.

Про суттєві зміни, що стосуються вже наявних прав, ми повідомимо, якщо цього вимагає закон.

## 16. Контактна інформація
Розробник: Максим Рождественський (techvault)
Країна: Україна
Сайт: https://www.techvault.tech
Загальні та юридичні питання: office@techvault.tech
Технічна підтримка: support@techvault.tech
Повернення коштів і платіжні спори: refund@techvault.tech
Адреса для юридичної кореспонденції: {ADDRESS_UK}

Переклади російською та українською мовами наведено для зручності; у разі розбіжностей переважну силу має англійська версія."""

# --------------------------------------------------------------------------- Privacy Policy
PRIVACY_EN = f"""Effective Date: November 9, 2026

techvault ("we", "us", or "our") respects your privacy and is committed to protecting your personal information.

This Privacy Policy describes how we collect, use, store, share, and protect personal data when you visit https://www.techvault.tech, create an account, purchase or use our software products, or contact our support team.

## 1. Data Controller
Name: Maksym Rozhdestvenskyi, operating as techvault
Country: Ukraine
Website: https://www.techvault.tech
Privacy Contact: office@techvault.tech
Correspondence address: {ADDRESS_EN}

For privacy-related requests, contact us at the email address above.

## 2. Information We Collect
Depending on your interactions with our services, we may process the following categories of information.

### Account Information
- Username and display name
- Email address
- Password authentication data, stored using secure password hashing
- Account creation and login records
- Account preferences

### Purchase and License Information
- Order identifiers
- Purchased products and license entitlements
- Transaction amounts, currency, and payment status
- Payment provider transaction references
- License activation and verification records

### Technical Information
- IP address
- Browser and operating system information
- Application version
- Device or installation identifiers, if used for licensing
- Error reports and diagnostic logs
- Security-related activity

### Support and Community Information
- Support messages and correspondence
- Bug reports and attachments you submit
- Forum posts, reviews, and feedback

We collect only information reasonably necessary for the purposes described in this Policy.

## 3. How We Use Personal Data
We process personal data to:
- Create and maintain user accounts.
- Authenticate users and protect accounts.
- Deliver purchased software and manage licenses.
- Verify purchases and prevent licensing fraud.
- Provide technical support.
- Process orders and refunds.
- Maintain software security and reliability.
- Diagnose errors and improve our products.
- Meet tax, accounting, and legal obligations.
- Send important account, purchase, security, and service notifications.
- Send optional promotional communications where permitted and appropriately authorized.

## 4. Legal Bases for Processing
Where the GDPR applies, processing may rely on:

Contractual necessity: to provide accounts, software access, licensing, purchases, and support.

Legal obligations: to maintain legally required accounting records and comply with applicable laws.

Legitimate interests: to protect systems, prevent fraud, investigate technical problems, and maintain service security, subject to applicable safeguards.

Consent: for optional analytics, marketing, or non-essential cookies where required.

You may withdraw consent at any time without affecting the lawfulness of processing performed before withdrawal.

## 5. Payment Processing
Payments may be handled by external payment processing providers.

These providers may collect payment information, perform fraud checks, and maintain transaction records under their own privacy policies.

techvault does not intentionally store complete credit or debit card numbers.

The applicable payment processor and its privacy information will be identified during checkout or in the relevant payment interface.

## 6. Cookies and Similar Technologies
Our website may use essential cookies or similar technologies for authentication, account sessions, security, and shopping functionality.

Non-essential analytics, advertising, or preference cookies will be used only in accordance with applicable consent requirements.

Where required, users will be offered the ability to accept, reject, or manage non-essential cookies.

## 7. Sharing of Information
We may disclose limited personal information to service providers necessary for operating our services, including:
- Website hosting and infrastructure providers
- Payment processors
- Transactional email services
- Security and anti-fraud providers
- Technical support and analytics services, where implemented

Service providers receive only the information required for their functions, subject to applicable contractual and legal safeguards.

We do not sell personal information to advertisers.

We may also disclose information where required by law or necessary to protect lawful rights.

## 8. International Data Transfers
Because techvault operates from Ukraine and may use infrastructure or service providers in other countries, personal data may be transferred internationally.

Where applicable data protection law requires safeguards for international transfers, we will implement appropriate measures, such as recognized contractual protections or other valid transfer mechanisms.

## 9. Data Retention
We retain personal data only for as long as reasonably necessary for the purpose for which it was collected, including:
- Account data while an account remains active and as otherwise required for legitimate purposes.
- Purchase and transaction records for applicable accounting, tax, and legal retention periods.
- License information while necessary to maintain valid software entitlements.
- Support and technical records for the time reasonably required to resolve issues and maintain security.

When data is no longer required, we delete or anonymize it, subject to legal obligations and legitimate retention needs.

## 10. Data Security
We implement appropriate technical and organizational measures designed to protect personal data.

These may include encrypted communications, access restrictions, secure authentication, and appropriate monitoring.

No online system can be guaranteed completely secure.

## 11. Your Privacy Rights
Depending on applicable law, you may have the right to:
- Request access to personal data.
- Correct inaccurate information.
- Request deletion of personal data.
- Restrict or object to certain processing.
- Receive portable copies of eligible data.
- Withdraw consent.
- Submit complaints to a competent data protection authority.

To exercise these rights, contact office@techvault.tech.

We will respond within the timeframes required by applicable law.

You may also lodge a complaint with the competent supervisory authority where the GDPR provides that right.

## 12. Account Deletion
You may request deletion of your account by contacting office@techvault.tech.

Account deletion may result in the loss of access to account-linked features and licenses. We will explain relevant consequences before completing a deletion request where required.

Certain transaction or legal records may need to be retained after account deletion.

## 13. Children's Privacy
Our services are not intended for children who are unable to provide valid consent or enter into the relevant agreement under applicable law without parental or guardian authorization.

We do not knowingly collect children's personal information in violation of applicable law.

If you believe such information has been collected improperly, please contact us.

## 14. Automated Decision-Making
We do not intend to use personal data for decisions based solely on automated processing that produce legal or similarly significant effects, unless separately disclosed with applicable safeguards.

Automated security or licensing checks may be used to verify valid access and detect suspicious activity.

## 15. Third-Party Websites
Our website may contain links to external services.

We are not responsible for third-party privacy practices. Please review their respective privacy policies.

## 16. Policy Updates
We may update this Privacy Policy to reflect changes in our services, data practices, or legal requirements.

The updated version will be published here with a revised effective date.

## 17. Contact
techvault — Maksym Rozhdestvenskyi
Country: Ukraine
Website: https://www.techvault.tech
Privacy and General Inquiries: office@techvault.tech
Technical Support: support@techvault.tech
Refund and Payment Inquiries: refund@techvault.tech"""

PRIVACY_RU = f"""Дата вступления в силу: 9 ноября 2026 г.

techvault («мы», «нас» или «наш») уважает вашу частную жизнь и стремится защищать ваши персональные данные.

Настоящая Политика конфиденциальности описывает, как мы собираем, используем, храним, передаём и защищаем персональные данные, когда вы посещаете https://www.techvault.tech, создаёте учётную запись, покупаете или используете наши программные продукты либо обращаетесь в службу поддержки.

## 1. Контролёр данных
Имя: Максим Рождественский, ведущий деятельность под названием techvault
Страна: Украина
Сайт: https://www.techvault.tech
Контакт по вопросам конфиденциальности: office@techvault.tech
Адрес для корреспонденции: {ADDRESS_RU}

С запросами, связанными с конфиденциальностью, обращайтесь по указанному выше адресу электронной почты.

## 2. Какие данные мы собираем
В зависимости от того, как вы пользуетесь нашими сервисами, мы можем обрабатывать следующие категории данных.

### Данные учётной записи
- Имя пользователя и отображаемое имя
- Адрес электронной почты
- Данные для аутентификации по паролю (хранятся в виде защищённого хеша)
- Записи о создании учётной записи и входах
- Настройки учётной записи

### Данные о покупках и лицензиях
- Идентификаторы заказов
- Купленные продукты и права по лицензиям
- Суммы транзакций, валюта и статус оплаты
- Идентификаторы транзакций платёжного провайдера
- Записи об активации и проверке лицензий

### Технические данные
- IP-адрес
- Сведения о браузере и операционной системе
- Версия приложения
- Идентификаторы устройства или установки, если они используются для лицензирования
- Отчёты об ошибках и диагностические журналы
- Действия, связанные с безопасностью

### Данные поддержки и сообщества
- Обращения в поддержку и переписка
- Отправленные вами сообщения об ошибках и вложения
- Сообщения на форуме, отзывы и обратная связь

Мы собираем только данные, обоснованно необходимые для целей, описанных в настоящей Политике.

## 3. Как мы используем персональные данные
Мы обрабатываем персональные данные, чтобы:
- Создавать и поддерживать учётные записи пользователей.
- Аутентифицировать пользователей и защищать учётные записи.
- Предоставлять купленное программное обеспечение и управлять лицензиями.
- Проверять покупки и предотвращать мошенничество с лицензиями.
- Оказывать техническую поддержку.
- Обрабатывать заказы и возвраты.
- Поддерживать безопасность и надёжность программ.
- Диагностировать ошибки и улучшать наши продукты.
- Выполнять налоговые, бухгалтерские и юридические обязательства.
- Отправлять важные уведомления об учётной записи, покупках, безопасности и работе сервиса.
- Отправлять необязательные рекламные сообщения, когда это разрешено и на это получено надлежащее согласие.

## 4. Правовые основания обработки
Если применяется GDPR, обработка может основываться на:

Договорной необходимости: для предоставления учётных записей, доступа к программам, лицензирования, покупок и поддержки.

Юридических обязательствах: для ведения обязательного бухгалтерского учёта и соблюдения применимого законодательства.

Законных интересах: для защиты систем, предотвращения мошенничества, расследования технических проблем и обеспечения безопасности сервиса — с соблюдением необходимых гарантий.

Согласии: для необязательной аналитики, маркетинга или необязательных файлов cookie, когда это требуется.

Вы можете отозвать согласие в любой момент; это не влияет на законность обработки, выполненной до отзыва.

## 5. Обработка платежей
Платежи могут обрабатываться внешними платёжными провайдерами.

Эти провайдеры могут собирать платёжные данные, проводить проверки на мошенничество и хранить записи о транзакциях в соответствии со своими политиками конфиденциальности.

techvault намеренно не хранит полные номера кредитных или дебетовых карт.

Платёжный провайдер и сведения о его политике конфиденциальности указываются при оформлении заказа или в соответствующем платёжном интерфейсе.

## 6. Файлы cookie и аналогичные технологии
Наш сайт может использовать необходимые файлы cookie или аналогичные технологии для аутентификации, сеансов учётной записи, безопасности и работы покупок.

Необязательные аналитические, рекламные файлы cookie или файлы cookie для сохранения настроек используются только в соответствии с применимыми требованиями о согласии.

Когда это требуется, пользователям предоставляется возможность принять, отклонить необязательные файлы cookie или управлять ими.

## 7. Передача данных
Мы можем передавать ограниченный объём персональных данных поставщикам услуг, необходимым для работы наших сервисов, в том числе:
- Хостинг-провайдерам и поставщикам инфраструктуры
- Платёжным провайдерам
- Сервисам транзакционной электронной почты
- Поставщикам решений для безопасности и защиты от мошенничества
- Сервисам технической поддержки и аналитики, если они используются

Поставщики услуг получают только данные, необходимые для выполнения их функций, с соблюдением договорных и правовых гарантий.

Мы не продаём персональные данные рекламодателям.

Мы также можем раскрывать данные, когда этого требует закон или когда это необходимо для защиты законных прав.

## 8. Международная передача данных
Поскольку techvault работает из Украины и может использовать инфраструктуру или поставщиков услуг в других странах, персональные данные могут передаваться за рубеж.

Если применимое законодательство о защите данных требует гарантий для международной передачи, мы применяем надлежащие меры, например признанные договорные механизмы защиты или другие действительные механизмы передачи.

## 9. Хранение данных
Мы храним персональные данные только в течение срока, обоснованно необходимого для целей, ради которых они были собраны, в том числе:
- Данные учётной записи — пока учётная запись активна и в иных случаях, когда это нужно для законных целей.
- Записи о покупках и транзакциях — в течение сроков, установленных бухгалтерским, налоговым и иным законодательством.
- Сведения о лицензиях — пока это необходимо для действия прав на программное обеспечение.
- Записи поддержки и технические записи — в течение времени, обоснованно необходимого для решения проблем и обеспечения безопасности.

Когда данные больше не нужны, мы удаляем или обезличиваем их с учётом требований закона и законной необходимости хранения.

## 10. Безопасность данных
Мы применяем надлежащие технические и организационные меры для защиты персональных данных.

К ним могут относиться шифрование соединений, ограничение доступа, защищённая аутентификация и надлежащий мониторинг.

Ни одна онлайн-система не может гарантировать полную безопасность.

## 11. Ваши права
В зависимости от применимого законодательства вы можете иметь право:
- Запросить доступ к своим персональным данным.
- Исправить неточные данные.
- Запросить удаление персональных данных.
- Ограничить определённую обработку или возразить против неё.
- Получить переносимые копии данных, на которые распространяется это право.
- Отозвать согласие.
- Подать жалобу в компетентный орган по защите данных.

Чтобы воспользоваться этими правами, напишите на office@techvault.tech.

Мы ответим в сроки, установленные применимым законодательством.

Вы также можете подать жалобу в компетентный надзорный орган, если такое право предусмотрено GDPR.

## 12. Удаление учётной записи
Вы можете запросить удаление учётной записи, написав на office@techvault.tech.

Удаление учётной записи может привести к потере доступа к связанным с ней функциям и лицензиям. Когда это требуется, мы объясним последствия до выполнения запроса.

Некоторые записи о транзакциях или юридически значимые записи может потребоваться сохранить и после удаления учётной записи.

## 13. Конфиденциальность детей
Наши сервисы не предназначены для детей, которые не могут дать действительное согласие или заключить соответствующий договор согласно применимому законодательству без разрешения родителей или законных представителей.

Мы сознательно не собираем персональные данные детей в нарушение применимого законодательства.

Если вы считаете, что такие данные были собраны ненадлежащим образом, свяжитесь с нами.

## 14. Автоматизированное принятие решений
Мы не планируем использовать персональные данные для решений, основанных исключительно на автоматизированной обработке и влекущих юридические или аналогично значимые последствия, если только это не будет отдельно раскрыто с соблюдением необходимых гарантий.

Для подтверждения законного доступа и выявления подозрительной активности могут использоваться автоматические проверки безопасности или лицензий.

## 15. Сторонние сайты
Наш сайт может содержать ссылки на внешние сервисы.

Мы не отвечаем за то, как сторонние сервисы обращаются с персональными данными. Пожалуйста, ознакомьтесь с их политиками конфиденциальности.

## 16. Обновление Политики
Мы можем обновлять настоящую Политику конфиденциальности с учётом изменений в наших сервисах, порядке обработки данных или требованиях законодательства.

Обновлённая версия будет опубликована на этой странице с новой датой вступления в силу.

## 17. Контакты
techvault — Максим Рождественский
Страна: Украина
Сайт: https://www.techvault.tech
Конфиденциальность и общие вопросы: office@techvault.tech
Техническая поддержка: support@techvault.tech
Возвраты и вопросы об оплате: refund@techvault.tech

Переводы на русский и украинский языки приведены для удобства; при расхождении преимущество имеет английская версия."""

PRIVACY_UK = f"""Дата набрання чинності: 9 листопада 2026 р.

techvault («ми», «нас» або «наш») поважає ваше приватне життя та прагне захищати ваші персональні дані.

Ця Політика конфіденційності описує, як ми збираємо, використовуємо, зберігаємо, передаємо та захищаємо персональні дані, коли ви відвідуєте https://www.techvault.tech, створюєте обліковий запис, купуєте чи використовуєте наші програмні продукти або звертаєтеся до служби підтримки.

## 1. Контролер даних
Ім'я: Максим Рождественський, який веде діяльність під назвою techvault
Країна: Україна
Сайт: https://www.techvault.tech
Контакт щодо конфіденційності: office@techvault.tech
Адреса для кореспонденції: {ADDRESS_UK}

Із запитами щодо конфіденційності звертайтеся за вказаною вище адресою електронної пошти.

## 2. Які дані ми збираємо
Залежно від того, як ви користуєтеся нашими сервісами, ми можемо обробляти такі категорії даних.

### Дані облікового запису
- Ім'я користувача та ім'я, що відображається
- Адреса електронної пошти
- Дані для автентифікації за паролем (зберігаються у вигляді захищеного хешу)
- Записи про створення облікового запису та входи
- Налаштування облікового запису

### Дані про покупки та ліцензії
- Ідентифікатори замовлень
- Придбані продукти та права за ліцензіями
- Суми транзакцій, валюта та статус оплати
- Ідентифікатори транзакцій платіжного провайдера
- Записи про активацію та перевірку ліцензій

### Технічні дані
- IP-адреса
- Відомості про браузер і операційну систему
- Версія застосунку
- Ідентифікатори пристрою або встановлення, якщо вони використовуються для ліцензування
- Звіти про помилки та діагностичні журнали
- Дії, пов'язані з безпекою

### Дані підтримки та спільноти
- Звернення до підтримки та листування
- Надіслані вами повідомлення про помилки та вкладення
- Повідомлення на форумі, відгуки та зворотний зв'язок

Ми збираємо лише дані, обґрунтовано необхідні для цілей, описаних у цій Політиці.

## 3. Як ми використовуємо персональні дані
Ми обробляємо персональні дані, щоб:
- Створювати та підтримувати облікові записи користувачів.
- Автентифікувати користувачів і захищати облікові записи.
- Надавати придбане програмне забезпечення та керувати ліцензіями.
- Перевіряти покупки та запобігати шахрайству з ліцензіями.
- Надавати технічну підтримку.
- Обробляти замовлення та повернення коштів.
- Підтримувати безпеку та надійність програм.
- Діагностувати помилки та вдосконалювати наші продукти.
- Виконувати податкові, бухгалтерські та юридичні зобов'язання.
- Надсилати важливі повідомлення щодо облікового запису, покупок, безпеки та роботи сервісу.
- Надсилати необов'язкові рекламні повідомлення, коли це дозволено та на це отримано належну згоду.

## 4. Правові підстави обробки
Якщо застосовується GDPR, обробка може ґрунтуватися на:

Договірній необхідності: для надання облікових записів, доступу до програм, ліцензування, покупок і підтримки.

Юридичних зобов'язаннях: для ведення обов'язкового бухгалтерського обліку та дотримання застосовного законодавства.

Законних інтересах: для захисту систем, запобігання шахрайству, розслідування технічних проблем і забезпечення безпеки сервісу — з дотриманням необхідних гарантій.

Згоді: для необов'язкової аналітики, маркетингу або необов'язкових файлів cookie, коли це потрібно.

Ви можете відкликати згоду будь-коли; це не впливає на законність обробки, здійсненої до відкликання.

## 5. Обробка платежів
Платежі можуть оброблятися зовнішніми платіжними провайдерами.

Ці провайдери можуть збирати платіжні дані, проводити перевірки на шахрайство та зберігати записи про транзакції відповідно до власних політик конфіденційності.

techvault навмисно не зберігає повних номерів кредитних або дебетових карток.

Платіжний провайдер і відомості про його політику конфіденційності зазначаються під час оформлення замовлення або у відповідному платіжному інтерфейсі.

## 6. Файли cookie та подібні технології
Наш сайт може використовувати необхідні файли cookie або подібні технології для автентифікації, сеансів облікового запису, безпеки та роботи покупок.

Необов'язкові аналітичні, рекламні файли cookie або файли cookie для збереження налаштувань використовуються лише відповідно до застосовних вимог щодо згоди.

Коли це потрібно, користувачам надається можливість прийняти, відхилити необов'язкові файли cookie або керувати ними.

## 7. Передача даних
Ми можемо передавати обмежений обсяг персональних даних постачальникам послуг, необхідним для роботи наших сервісів, зокрема:
- Хостинг-провайдерам і постачальникам інфраструктури
- Платіжним провайдерам
- Сервісам транзакційної електронної пошти
- Постачальникам рішень для безпеки та захисту від шахрайства
- Сервісам технічної підтримки та аналітики, якщо вони використовуються

Постачальники послуг отримують лише дані, необхідні для виконання своїх функцій, з дотриманням договірних і правових гарантій.

Ми не продаємо персональні дані рекламодавцям.

Ми також можемо розкривати дані, коли цього вимагає закон або коли це необхідно для захисту законних прав.

## 8. Міжнародна передача даних
Оскільки techvault працює з України та може використовувати інфраструктуру або постачальників послуг в інших країнах, персональні дані можуть передаватися за кордон.

Якщо застосовне законодавство про захист даних вимагає гарантій для міжнародної передачі, ми застосовуємо належні заходи, наприклад визнані договірні механізми захисту або інші дійсні механізми передачі.

## 9. Зберігання даних
Ми зберігаємо персональні дані лише протягом строку, обґрунтовано необхідного для цілей, заради яких їх було зібрано, зокрема:
- Дані облікового запису — поки обліковий запис активний та в інших випадках, коли це потрібно для законних цілей.
- Записи про покупки та транзакції — протягом строків, установлених бухгалтерським, податковим та іншим законодавством.
- Відомості про ліцензії — поки це необхідно для дії прав на програмне забезпечення.
- Записи підтримки та технічні записи — протягом часу, обґрунтовано необхідного для вирішення проблем і забезпечення безпеки.

Коли дані більше не потрібні, ми видаляємо або знеособлюємо їх з урахуванням вимог закону та законної необхідності зберігання.

## 10. Безпека даних
Ми застосовуємо належні технічні та організаційні заходи для захисту персональних даних.

До них можуть належати шифрування з'єднань, обмеження доступу, захищена автентифікація та належний моніторинг.

Жодна онлайн-система не може гарантувати повної безпеки.

## 11. Ваші права
Залежно від застосовного законодавства ви можете мати право:
- Запитати доступ до своїх персональних даних.
- Виправити неточні дані.
- Запитати видалення персональних даних.
- Обмежити певну обробку або заперечити проти неї.
- Отримати переносні копії даних, на які поширюється це право.
- Відкликати згоду.
- Подати скаргу до компетентного органу із захисту даних.

Щоб скористатися цими правами, напишіть на office@techvault.tech.

Ми відповімо у строки, встановлені застосовним законодавством.

Ви також можете подати скаргу до компетентного наглядового органу, якщо таке право передбачено GDPR.

## 12. Видалення облікового запису
Ви можете запитати видалення облікового запису, написавши на office@techvault.tech.

Видалення облікового запису може призвести до втрати доступу до пов'язаних із ним функцій і ліцензій. Коли це потрібно, ми пояснимо наслідки до виконання запиту.

Деякі записи про транзакції або юридично значущі записи може знадобитися зберегти й після видалення облікового запису.

## 13. Конфіденційність дітей
Наші сервіси не призначені для дітей, які не можуть надати дійсну згоду або укласти відповідний договір згідно із застосовним законодавством без дозволу батьків чи законних представників.

Ми свідомо не збираємо персональні дані дітей з порушенням застосовного законодавства.

Якщо ви вважаєте, що такі дані було зібрано неналежним чином, зв'яжіться з нами.

## 14. Автоматизоване ухвалення рішень
Ми не плануємо використовувати персональні дані для рішень, що ґрунтуються виключно на автоматизованій обробці та мають юридичні або подібні значущі наслідки, якщо тільки це не буде окремо розкрито з дотриманням необхідних гарантій.

Для підтвердження законного доступу та виявлення підозрілої активності можуть використовуватися автоматичні перевірки безпеки або ліцензій.

## 15. Сторонні сайти
Наш сайт може містити посилання на зовнішні сервіси.

Ми не відповідаємо за те, як сторонні сервіси поводяться з персональними даними. Будь ласка, ознайомтеся з їхніми політиками конфіденційності.

## 16. Оновлення Політики
Ми можемо оновлювати цю Політику конфіденційності з урахуванням змін у наших сервісах, порядку обробки даних або вимогах законодавства.

Оновлену версію буде опубліковано на цій сторінці з новою датою набрання чинності.

## 17. Контакти
techvault — Максим Рождественський
Країна: Україна
Сайт: https://www.techvault.tech
Конфіденційність і загальні питання: office@techvault.tech
Технічна підтримка: support@techvault.tech
Повернення коштів і питання оплати: refund@techvault.tech

Переклади російською та українською мовами наведено для зручності; у разі розбіжностей переважну силу має англійська версія."""

# --------------------------------------------------------------------------- Refund Policy
REFUNDS_EN = """Effective Date: November 9, 2026

Thank you for purchasing software from techvault.

This Refund Policy explains how refunds are handled for digital software, applications, games, license keys, subscriptions, Early Access products, and other digital purchases made through https://www.techvault.tech.

Developer: Maksym Rozhdestvenskyi (techvault)
Refund Contact: refund@techvault.tech

## 1. Digital Product Delivery
Our products are primarily distributed electronically.

After successful payment, purchased software or license entitlements may be made available through your techvault account, a download link, a license key, or another delivery method specified during checkout.

No physical goods are shipped unless expressly stated otherwise.

## 2. Voluntary Refund Eligibility
Subject to applicable law, we offer a voluntary refund request period of 14 calendar days from the purchase date for digital products that have not been downloaded, activated, or accessed.

We may also consider refund requests for:
- Duplicate purchases or accidental duplicate charges.
- Technical failures that prevent the purchased product from functioning as described and cannot be reasonably resolved.
- Failure to deliver a purchased product or valid license.
- Incorrect charges or other billing errors.

Refund eligibility is assessed according to the circumstances, applicable legal requirements, and the payment provider's procedures.

## 3. Downloaded or Activated Software
Digital products that have already been downloaded, activated, or accessed may not qualify for a voluntary change-of-mind refund.

Where applicable law permits the loss of a statutory withdrawal right for immediately supplied digital content, this depends on obtaining the customer's required prior express consent and acknowledgment and providing the required purchase confirmation.

This restriction does not affect mandatory consumer rights concerning defective, non-conforming, or undelivered digital content.

## 4. Early Access, Beta, and Pre-Release Products
Certain software products may be distributed in Early Access, beta, or pre-release versions.

These products are under development and may contain bugs, incomplete functionality, compatibility limitations, or performance issues.

The development status and known limitations disclosed before purchase form part of the product description.

Refund requests based solely on a clearly disclosed pre-release characteristic may not qualify for a voluntary refund after access begins.

However, technical defects, failure to deliver, material non-conformity, or other circumstances protected by applicable law remain eligible for the remedies required by law.

## 5. Subscription Products
Where subscription-based products are offered, renewal terms, billing frequency, and cancellation conditions will be disclosed before purchase.

Cancelling a subscription ordinarily prevents future renewals but does not automatically result in a refund for an already-started billing period, except where required by law or stated in the applicable offer.

## 6. How to Request a Refund
To request a refund, contact:
refund@techvault.tech

Please include:
- Your order number or transaction reference.
- The email address associated with your purchase.
- The product name.
- The date of purchase.
- A brief description of the issue.
- Relevant error messages or screenshots, if available.

Do not send payment card numbers, passwords, or other sensitive authentication information.

## 7. Refund Review and Processing
We aim to acknowledge refund requests within 3 business days.

We may request additional information or offer troubleshooting where this is appropriate and does not interfere with your statutory rights.

Approved refunds are generally initiated through the original payment method, unless otherwise permitted or required by law.

Actual processing times depend on the payment service provider, the issuing bank, and applicable legal deadlines.

## 8. Cancellation of License Access
When a purchase is refunded, the associated software license or entitlement may be revoked.

Users must discontinue use of software for which the underlying license has been validly cancelled and remove copies where required by the applicable license agreement and law.

Refunding one product does not automatically terminate access to unrelated purchases.

## 9. Purchases Through Third-Party Platforms
If you purchased a techvault product through an external marketplace or distributor acting as the seller or merchant of record, the applicable platform's refund procedure may govern the transaction.

We will provide reasonable assistance in identifying the appropriate refund channel.

Nothing in this section limits mandatory rights against the legally responsible seller.

## 10. Chargebacks and Payment Disputes
If you believe a payment was unauthorized or incorrect, contact refund@techvault.tech or your payment provider.

We may investigate disputed transactions and temporarily restrict affected entitlements where necessary to prevent fraud, subject to applicable law.

## 11. Consumer Protection Rights
This Policy does not replace, exclude, or restrict any statutory cancellation, conformity, repair, replacement, price reduction, termination, or refund rights available under applicable consumer protection laws.

In particular, customers in jurisdictions with mandatory digital content consumer protections retain those protections regardless of any voluntary refund limitations described above.

## 12. Changes to This Policy
We may update this Refund Policy from time to time.

Updates will be published on this page with the revised effective date.

Changes will not retroactively remove rights established under an existing purchase or applicable law.

## 13. Contact Information
techvault
Developer: Maksym Rozhdestvenskyi
Country: Ukraine
Website: https://www.techvault.tech
Refunds and Billing Disputes: refund@techvault.tech
General and Legal Inquiries: office@techvault.tech
Technical Support: support@techvault.tech

For refund requests, include your purchase reference and a description of the problem."""

REFUNDS_RU = """Дата вступления в силу: 9 ноября 2026 г.

Спасибо, что приобрели программное обеспечение techvault.

Настоящие Правила возврата объясняют, как осуществляются возвраты за цифровое программное обеспечение, приложения, игры, лицензионные ключи, подписки, продукты раннего доступа (Early Access) и другие цифровые покупки, совершённые через https://www.techvault.tech.

Разработчик: Максим Рождественский (techvault)
Контакт по вопросам возврата: refund@techvault.tech

## 1. Доставка цифровых продуктов
Наши продукты распространяются преимущественно в электронном виде.

После успешной оплаты купленное программное обеспечение или права по лицензии могут предоставляться через вашу учётную запись techvault, ссылку для скачивания, лицензионный ключ или иным способом, указанным при оформлении заказа.

Физические товары не отправляются, если прямо не указано иное.

## 2. Добровольный возврат
С учётом применимого законодательства мы предоставляем возможность добровольно запросить возврат в течение 14 календарных дней с даты покупки за цифровые продукты, которые не были скачаны, активированы и к которым не был получен доступ.

Мы также можем рассмотреть запросы на возврат в случаях:
- Повторной покупки или случайного двойного списания.
- Технических сбоев, из-за которых купленный продукт не работает так, как описано, и которые невозможно обоснованно устранить.
- Непредоставления купленного продукта или действительной лицензии.
- Неверного списания или других ошибок при выставлении счёта.

Право на возврат оценивается с учётом обстоятельств, требований применимого законодательства и процедур платёжного провайдера.

## 3. Скачанное или активированное программное обеспечение
Цифровые продукты, которые уже были скачаны, активированы или к которым был получен доступ, могут не подлежать добровольному возврату по причине того, что вы передумали.

Если применимое законодательство допускает утрату предусмотренного законом права на отказ от покупки цифрового контента, предоставляемого сразу, это возможно только при получении предварительного явного согласия и подтверждения покупателя и предоставлении требуемого подтверждения покупки.

Это ограничение не затрагивает обязательных прав потребителя в отношении дефектного, не соответствующего описанию или не предоставленного цифрового контента.

## 4. Ранний доступ, бета- и предварительные версии
Некоторые программные продукты могут распространяться в версиях раннего доступа, бета- или предварительных версиях.

Такие продукты находятся в разработке и могут содержать ошибки, незавершённые функции, ограничения совместимости или проблемы с производительностью.

Статус разработки и известные ограничения, раскрытые до покупки, являются частью описания продукта.

Запросы на возврат, основанные исключительно на явно указанной особенности предварительной версии, могут не подлежать добровольному возврату после получения доступа.

Однако при технических дефектах, непредоставлении продукта, существенном несоответствии описанию или иных обстоятельствах, защищённых применимым законодательством, сохраняются средства защиты, предусмотренные законом.

## 5. Продукты по подписке
Если предлагаются продукты по подписке, условия продления, периодичность списаний и условия отмены раскрываются до покупки.

Отмена подписки, как правило, прекращает её будущие продления, но не влечёт автоматического возврата за уже начавшийся расчётный период, кроме случаев, когда этого требует закон или это указано в соответствующем предложении.

## 6. Как запросить возврат
Чтобы запросить возврат, напишите на адрес:
refund@techvault.tech

Пожалуйста, укажите:
- Номер заказа или идентификатор транзакции.
- Адрес электронной почты, связанный с покупкой.
- Название продукта.
- Дату покупки.
- Краткое описание проблемы.
- Сообщения об ошибках или снимки экрана, если они есть.

Не отправляйте номера платёжных карт, пароли и другие конфиденциальные данные для аутентификации.

## 7. Рассмотрение и обработка возврата
Мы стремимся подтверждать получение запросов на возврат в течение 3 рабочих дней.

Мы можем запросить дополнительную информацию или предложить помощь в устранении проблемы, если это уместно и не ущемляет ваших прав, предусмотренных законом.

Одобренные возвраты, как правило, осуществляются тем же способом, которым была произведена оплата, если иное не разрешено или не требуется законом.

Фактические сроки зачисления зависят от платёжного провайдера, банка-эмитента и сроков, установленных применимым законодательством.

## 8. Прекращение доступа по лицензии
При возврате средств за покупку связанная с ней лицензия или право на программное обеспечение может быть отозвано.

Пользователь обязан прекратить использование программного обеспечения, лицензия на которое была правомерно аннулирована, и удалить копии, если этого требуют применимое лицензионное соглашение и законодательство.

Возврат за один продукт не прекращает автоматически доступ к другим, не связанным с ним покупкам.

## 9. Покупки через сторонние платформы
Если вы купили продукт techvault через внешнюю торговую площадку или дистрибьютора, выступающего продавцом или официальным реселлером (Merchant of Record), к такой покупке может применяться порядок возврата этой платформы.

Мы окажем разумное содействие в определении подходящего способа получения возврата.

Ничто в этом разделе не ограничивает обязательных прав в отношении продавца, несущего юридическую ответственность.

## 10. Чарджбэки и платёжные споры
Если вы считаете, что платёж был несанкционированным или ошибочным, обратитесь на refund@techvault.tech или к своему платёжному провайдеру.

Мы можем проверять оспариваемые транзакции и временно ограничивать связанные с ними права, если это необходимо для предотвращения мошенничества, с учётом применимого законодательства.

## 11. Права потребителей
Настоящие Правила не заменяют, не исключают и не ограничивают предусмотренные законом права на отказ от покупки, соответствие товара, ремонт, замену, снижение цены, расторжение договора или возврат средств, предоставляемые применимым законодательством о защите прав потребителей.

В частности, покупатели в юрисдикциях с обязательной защитой прав потребителей цифрового контента сохраняют эту защиту независимо от описанных выше ограничений добровольного возврата.

## 12. Изменение Правил
Мы можем время от времени обновлять настоящие Правила возврата.

Обновления публикуются на этой странице с новой датой вступления в силу.

Изменения не отменяют задним числом права, возникшие в связи с уже совершённой покупкой или в силу применимого законодательства.

## 13. Контактная информация
techvault
Разработчик: Максим Рождественский
Страна: Украина
Сайт: https://www.techvault.tech
Возвраты и платёжные споры: refund@techvault.tech
Общие и юридические вопросы: office@techvault.tech
Техническая поддержка: support@techvault.tech

В запросе на возврат укажите идентификатор покупки и описание проблемы.

Переводы на русский и украинский языки приведены для удобства; при расхождении преимущество имеет английская версия."""

REFUNDS_UK = """Дата набрання чинності: 9 листопада 2026 р.

Дякуємо, що придбали програмне забезпечення techvault.

Ці Правила повернення пояснюють, як здійснюється повернення коштів за цифрове програмне забезпечення, застосунки, ігри, ліцензійні ключі, підписки, продукти раннього доступу (Early Access) та інші цифрові покупки, здійснені через https://www.techvault.tech.

Розробник: Максим Рождественський (techvault)
Контакт щодо повернення коштів: refund@techvault.tech

## 1. Доставка цифрових продуктів
Наші продукти поширюються переважно в електронному вигляді.

Після успішної оплати придбане програмне забезпечення або права за ліцензією можуть надаватися через ваш обліковий запис techvault, посилання для завантаження, ліцензійний ключ або в інший спосіб, зазначений під час оформлення замовлення.

Фізичні товари не надсилаються, якщо прямо не зазначено інше.

## 2. Добровільне повернення коштів
З урахуванням застосовного законодавства ми надаємо можливість добровільно запросити повернення коштів протягом 14 календарних днів з дати покупки за цифрові продукти, які не були завантажені, активовані та до яких не було отримано доступу.

Ми також можемо розглянути запити на повернення у випадках:
- Повторної покупки або випадкового подвійного списання.
- Технічних збоїв, через які придбаний продукт не працює так, як описано, і які неможливо обґрунтовано усунути.
- Ненадання придбаного продукту або дійсної ліцензії.
- Неправильного списання чи інших помилок під час виставлення рахунку.

Право на повернення оцінюється з урахуванням обставин, вимог застосовного законодавства та процедур платіжного провайдера.

## 3. Завантажене або активоване програмне забезпечення
Цифрові продукти, які вже були завантажені, активовані або до яких було отримано доступ, можуть не підлягати добровільному поверненню через те, що ви передумали.

Якщо застосовне законодавство допускає втрату передбаченого законом права на відмову від покупки цифрового контенту, що надається одразу, це можливо лише за умови отримання попередньої явної згоди та підтвердження покупця і надання необхідного підтвердження покупки.

Це обмеження не стосується обов'язкових прав споживача щодо дефектного, невідповідного опису або ненаданого цифрового контенту.

## 4. Ранній доступ, бета- та попередні версії
Деякі програмні продукти можуть поширюватися у версіях раннього доступу, бета- або попередніх версіях.

Такі продукти перебувають у розробці та можуть містити помилки, незавершені функції, обмеження сумісності або проблеми з продуктивністю.

Статус розробки та відомі обмеження, розкриті до покупки, є частиною опису продукту.

Запити на повернення, що ґрунтуються виключно на явно зазначеній особливості попередньої версії, можуть не підлягати добровільному поверненню після отримання доступу.

Проте в разі технічних дефектів, ненадання продукту, суттєвої невідповідності опису або інших обставин, захищених застосовним законодавством, зберігаються засоби захисту, передбачені законом.

## 5. Продукти за підпискою
Якщо пропонуються продукти за підпискою, умови продовження, періодичність списань та умови скасування розкриваються до покупки.

Скасування підписки, як правило, припиняє її майбутні продовження, але не тягне за собою автоматичного повернення коштів за вже розпочатий розрахунковий період, крім випадків, коли цього вимагає закон або це зазначено у відповідній пропозиції.

## 6. Як запросити повернення коштів
Щоб запросити повернення, напишіть на адресу:
refund@techvault.tech

Будь ласка, зазначте:
- Номер замовлення або ідентифікатор транзакції.
- Адресу електронної пошти, пов'язану з покупкою.
- Назву продукту.
- Дату покупки.
- Короткий опис проблеми.
- Повідомлення про помилки або знімки екрана, якщо вони є.

Не надсилайте номерів платіжних карток, паролів та інших конфіденційних даних для автентифікації.

## 7. Розгляд і обробка повернення
Ми прагнемо підтверджувати отримання запитів на повернення протягом 3 робочих днів.

Ми можемо запитати додаткову інформацію або запропонувати допомогу в усуненні проблеми, якщо це доречно та не обмежує ваших прав, передбачених законом.

Схвалені повернення, як правило, здійснюються тим самим способом, яким було здійснено оплату, якщо інше не дозволено або не вимагається законом.

Фактичні строки зарахування залежать від платіжного провайдера, банку-емітента та строків, установлених застосовним законодавством.

## 8. Припинення доступу за ліцензією
У разі повернення коштів за покупку пов'язана з нею ліцензія або право на програмне забезпечення може бути відкликано.

Користувач зобов'язаний припинити використання програмного забезпечення, ліцензію на яке було правомірно анульовано, і видалити копії, якщо цього вимагають застосовна ліцензійна угода та законодавство.

Повернення коштів за один продукт не припиняє автоматично доступу до інших, не пов'язаних із ним покупок.

## 9. Покупки через сторонні платформи
Якщо ви придбали продукт techvault через зовнішній маркетплейс або дистриб'ютора, що діє як продавець або офіційний реселер (Merchant of Record), до такої покупки може застосовуватися порядок повернення цієї платформи.

Ми надамо розумне сприяння у визначенні відповідного способу отримання повернення.

Ніщо в цьому розділі не обмежує обов'язкових прав щодо продавця, який несе юридичну відповідальність.

## 10. Чарджбеки та платіжні спори
Якщо ви вважаєте, що платіж був несанкціонованим або помилковим, зверніться на refund@techvault.tech або до свого платіжного провайдера.

Ми можемо перевіряти оскаржувані транзакції та тимчасово обмежувати пов'язані з ними права, якщо це необхідно для запобігання шахрайству, з урахуванням застосовного законодавства.

## 11. Права споживачів
Ці Правила не замінюють, не виключають і не обмежують передбачених законом прав на відмову від покупки, відповідність товару, ремонт, заміну, зниження ціни, розірвання договору або повернення коштів, що надаються застосовним законодавством про захист прав споживачів.

Зокрема, покупці в юрисдикціях з обов'язковим захистом прав споживачів цифрового контенту зберігають цей захист незалежно від описаних вище обмежень добровільного повернення.

## 12. Зміна Правил
Ми можемо час від часу оновлювати ці Правила повернення.

Оновлення публікуються на цій сторінці з новою датою набрання чинності.

Зміни не скасовують заднім числом прав, що виникли у зв'язку з уже здійсненою покупкою або в силу застосовного законодавства.

## 13. Контактна інформація
techvault
Розробник: Максим Рождественський
Країна: Україна
Сайт: https://www.techvault.tech
Повернення коштів і платіжні спори: refund@techvault.tech
Загальні та юридичні питання: office@techvault.tech
Технічна підтримка: support@techvault.tech

У запиті на повернення зазначте ідентифікатор покупки та опис проблеми.

Переклади російською та українською мовами наведено для зручності; у разі розбіжностей переважну силу має англійська версія."""

PAGES = [
    ("terms", 1, ("Условия использования", "Terms of Service", "Умови використання"), (TERMS_RU, TERMS_EN, TERMS_UK)),
    ("privacy", 2, ("Политика конфиденциальности", "Privacy Policy", "Політика конфіденційності"),
     (PRIVACY_RU, PRIVACY_EN, PRIVACY_UK)),
    ("refunds", 3, ("Правила возврата", "Refund Policy", "Правила повернення коштів"),
     (REFUNDS_RU, REFUNDS_EN, REFUNDS_UK)),
]


def load_pages(apps, schema_editor):
    Page = apps.get_model("core", "Page")
    for slug, order, (t_ru, t_en, t_uk), (b_ru, b_en, b_uk) in PAGES:
        Page.objects.update_or_create(slug=slug, defaults={
            "order": order, "title_ru": t_ru, "title_en": t_en, "title_uk": t_uk,
            "body_ru": b_ru, "body_en": b_en, "body_uk": b_uk,
            "show_in_footer": True, "is_published": True,
        })


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_legal_pages"),
    ]

    operations = [
        migrations.RunPython(load_pages, migrations.RunPython.noop),
    ]
