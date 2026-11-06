# Развёртывание TechVault на Ubuntu Server

Схема: **nginx** (HTTPS от Let's Encrypt, статика, обложки и аватары) → **gunicorn** (Django, сервис systemd)
→ **PostgreSQL** (база) + **Redis** (общий кеш). Проверено для Ubuntu 22.04 и 24.04.

```
Интернет ──443──> nginx ──/run/django-site.sock──> gunicorn (Django) ──> PostgreSQL
                    │                                              └──> Redis
                    ├── /static/              → /var/www/django-site/staticfiles
                    ├── /media/covers|avatars → /var/www/django-site/media
                    └── /protected-media/ (internal) ← X-Accel-Redirect после проверки покупки
```

| Что | Где |
|---|---|
| Код (git-репозиторий, manage.py) | `/var/www/django-site` |
| Виртуальное окружение | `/var/www/django-site/venv` |
| Загруженные файлы (обложки, аватары, установщики) | `/var/www/django-site/media` |
| Собранная статика | `/var/www/django-site/staticfiles` |
| Сокет gunicorn | `/run/django-site.sock` (создаёт `django-site.socket`) |
| Конфиг nginx | `/etc/nginx/sites-available/django-site` |
| Настройки и секреты | `/etc/techvault/techvault.env` (640, root:techvault) |
| Сервис | `django-site.service` + `django-site.socket` (пользователь `techvault`) |
| Резервные копии | `/var/backups/techvault` |

## Запуск techvault.tech — коротко

Что уже проверено по DNS (6 ноября 2026): `techvault.tech` и `www.techvault.tech` указывают на
**72.60.17.152** (VPS Hostinger, IPv6 `2a02:4780:c:a2ee::1`), почта домена — **Hostinger Mail**
(`mx1/mx2.hostinger.com`, SPF настроен). На сервере уже отвечает nginx (страница по умолчанию),
а **порт 443 закрыт** — откройте его до установки.

1. **Откройте порты 80 и 443** в hPanel Hostinger: VPS → Безопасность → Файрвол (если он включён).
   Если на сервере включён `ufw`, install.sh сам разрешит «Nginx Full».
2. **Проверьте IPv6**: на сервере выполните `ip -6 addr show scope global`. Если адреса
   `2a02:4780:c:a2ee::1` там нет — удалите AAAA-запись в DNS Hostinger, иначе Let's Encrypt не выдаст
   сертификат (install.sh тоже предупредит).
3. **Код на сервер.** Отправьте ветку в GitHub со своего компьютера:

   ```powershell
   git push -u origin deploy-ubuntu
   ```

4. **Прежний проект.** Если в `/var/www/django-site` уже лежит другой проект (не этот git-репозиторий),
   перенесите его — install.sh не станет ничего затирать и остановится с подсказкой:

   ```bash
   sudo mv /var/www/django-site /var/www/django-site.old
   ```

   Прежние юниты systemd, которые слушают `/run/django-site.sock`, и прежний конфиг nginx для домена
   install.sh отключит сам и сохранит их копии с суффиксом `.bak-<дата>`.

5. **Установка** (на сервере, под пользователем с sudo):

   ```bash
   git clone -b deploy-ubuntu https://github.com/MaksStalker1985/mywebproject.git /tmp/techvault
   sudo DOMAIN=techvault.tech WWW=1 LETSENCRYPT_EMAIL=support@techvault.tech \
        ADMIN_EMAIL=support@techvault.tech \
        REPO_URL=https://github.com/MaksStalker1985/mywebproject.git BRANCH=deploy-ubuntu \
        bash /tmp/techvault/deploy/install.sh
   ```

   Если репозиторий приватный — на сервере понадобится доступ к нему (deploy key или токен).
   По ходу установки скрипт спросит:
   - **пароль почтового ящика `support@techvault.tech`** — для отправки писем через `smtp.hostinger.com:465`;
   - **пароль администратора сайта** (логин `admin`) — придумайте отдельный надёжный пароль,
     не совпадающий с паролем почты.

   Пароли вводятся только в терминале сервера и сохраняются в `/etc/techvault/techvault.env`
   (доступ только у root и сервиса) — в git и в код они не попадают.
6. **Реквизиты продавца.** Войдите `https://techvault.tech/ru/manage/` → **Страницы** и в
   «Условия использования» и «Политика конфиденциальности» замените строку в квадратных скобках на
   ФОП/компанию, страну и адрес. Платёжные системы проверяют эти страницы перед подключением.
7. **Платежи.** Впишите ключи Paddle (или Stripe) в `/etc/techvault/techvault.env`,
   `sudo systemctl restart django-site`. Адреса для Paddle: Default payment link
   `https://techvault.tech/payments/paddle/pay/`, уведомления `https://techvault.tech/payments/webhook/paddle/`.
8. **Каталог.** Добавьте игры и программы через **Панель управления → Игры и ПО**, создайте разделы форума.
9. **Проверка почты.** Выйдите и нажмите «Забыли пароль?» — письмо должно прийти с `support@techvault.tech`.
   Чтобы письма не попадали в спам, в hPanel → Почта → Настройки DNS включите **DKIM** и добавьте **DMARC**
   (SPF уже есть).

## 1. Что нужно заранее

- Сервер с Ubuntu, доступ по SSH с правами sudo. Хватит 1–2 vCPU и 2 ГБ RAM; место на диске — под
  установочные файлы игр.
- Домен, у которого **A-запись** (и AAAA для IPv6) указывает на IP сервера, — без этого Let's Encrypt не
  выдаст сертификат.
- Открытые порты 22, 80, 443. Если включаете файрвол:

  ```bash
  sudo ufw allow OpenSSH && sudo ufw allow "Nginx Full" && sudo ufw enable
  ```

## 2. Перенести код на сервер

**Вариант А — через git (удобнее для обновлений).** Отправьте проект в приватный репозиторий
(GitHub, GitLab), на сервере установщик склонирует его сам. Для приватного репозитория добавьте на сервер
deploy key или используйте HTTPS-токен.

**Вариант Б — копированием** с вашего компьютера (PowerShell, без `.venv`, базы и `media`):

```powershell
git archive --format=tar.gz -o techvault.tar.gz HEAD
scp techvault.tar.gz user@SERVER:/tmp/
```

```bash
sudo mkdir -p /var/www/django-site && sudo tar -xzf /tmp/techvault.tar.gz -C /var/www/django-site
```

`git archive` берёт только закоммиченные файлы — сначала закоммитьте изменения.

## 3. Установка

Вариант А:

```bash
git clone https://github.com/you/techvault.git /tmp/techvault
sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com \
     REPO_URL=https://github.com/you/techvault.git bash /tmp/techvault/deploy/install.sh
```

Вариант Б:

```bash
sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com bash /var/www/django-site/deploy/install.sh
```

Добавьте `WWW=1`, если нужен ещё и `www.example.com`. Без `LETSENCRYPT_EMAIL` сайт поднимется по HTTP —
удобно для первой проверки; потом запустите скрипт ещё раз с e-mail.

Скрипт ставит пакеты, создаёт системного пользователя `techvault`, базу PostgreSQL со случайным паролем,
`/etc/techvault/techvault.env` со случайным `DJANGO_SECRET_KEY`, применяет миграции, собирает статику,
запускает сервис, настраивает nginx и получает сертификат. Повторный запуск безопасен: пароли, база,
`.env` и nginx-конфиг с сертификатом не перезаписываются.

## 4. После установки

1. **Администратор** (демо-данные `seed_demo` на сервере не запускайте — у них известные пароли; команда
   и не запустится при `DJANGO_DEBUG=0`):

   ```bash
   sudo techvault-manage createsuperuser
   ```

2. **Почта** — без неё не работают «Забыли пароль?» и уведомления формы связи. Впишите SMTP
   (своего почтового сервиса: Mailgun, SendGrid, Яндекс 360, Google Workspace…):

   ```bash
   sudo nano /etc/techvault/techvault.env     # EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
   sudo systemctl restart django-site
   ```

   Чтобы письма не попадали в спам, настройте у домена SPF, DKIM и DMARC по инструкции почтового сервиса.

3. **Платежи** — в том же файле: `PAYMENTS_PROVIDER` (`paddle` или `stripe`), `PAYMENTS_CURRENCY` и ключи.
   Адреса для кабинета платёжной системы:
   - Paddle: Default payment link `https://example.com/payments/paddle/pay/`,
     уведомления `https://example.com/payments/webhook/paddle/`;
   - Stripe: webhook `https://example.com/payments/webhook/stripe/`.

4. **Разделы форума и каталог** — заполните через панель управления `https://example.com/ru/manage/`.

5. **HSTS** — когда убедитесь, что HTTPS работает, увеличьте `DJANGO_HSTS_SECONDS=31536000`.
   `DJANGO_HSTS_SUBDOMAINS=1` включайте, только если все поддомены тоже работают по HTTPS.

## 5. Обновление

После изменений в коде:

```bash
sudo bash /var/www/django-site/deploy/update.sh            # git pull + зависимости + миграции + статика + перезапуск
```

Если код копируете архивом: распакуйте его поверх `/var/www/django-site` и запустите
`sudo NO_PULL=1 bash /var/www/django-site/deploy/update.sh`.

## 6. Резервные копии

```bash
sudo bash /var/www/django-site/deploy/backup.sh            # база + media + .env в /var/backups/techvault
sudo crontab -e                                          # ежедневно в 03:30:
# 30 3 * * * /bin/bash /var/www/django-site/deploy/backup.sh >/var/log/techvault-backup.log 2>&1
```

Копии старше 14 дней удаляются. Храните копии ещё и вне сервера (rsync, S3, облачный диск) — копия на том
же диске не спасёт при его потере. Команды восстановления — в конце `deploy/backup.sh`.

## 7. Диагностика

| Проблема | Что смотреть |
|---|---|
| 502 Bad Gateway | `sudo systemctl status django-site django-site.socket`, `sudo journalctl -u django-site -n 100` |
| 400 Bad Request | домен не в `DJANGO_ALLOWED_HOSTS` |
| 403 CSRF при отправке форм | адрес сайта не в `DJANGO_CSRF_TRUSTED_ORIGINS` (с `https://`) |
| Нет стилей | `sudo techvault-manage collectstatic --noinput`, права на `/var/www/django-site/staticfiles` |
| Не скачиваются игры | файл есть в `/var/www/django-site/media/downloads`, `DJANGO_DOWNLOADS_ACCEL_PREFIX=/protected-media` |
| Ошибки nginx | `sudo nginx -t`, `sudo tail -f /var/log/nginx/error.log` |
| Не приходят письма | `sudo journalctl -u django-site | grep -i smtp`, настройки SMTP |
| Сертификат | `sudo certbot renew --dry-run` (продление автоматическое, таймер certbot) |

## Безопасность — что уже сделано

- `DJANGO_DEBUG=0`, без `DJANGO_SECRET_KEY` сайт не запускается; `manage.py check --deploy` при установке.
- HTTPS-редирект, cookie только по HTTPS, HSTS, `X-Frame-Options: DENY`, `nosniff`.
- Установочные файлы платных игр недоступны по прямой ссылке: nginx отдаёт их только после проверки покупки
  в Django (`X-Accel-Redirect`). Напрямую открыты лишь обложки и аватары.
- gunicorn работает от отдельного пользователя без shell, с ограничениями systemd (запись только в `media`).
- Секреты — в `/etc/techvault/techvault.env`, не в коде и не в git.
