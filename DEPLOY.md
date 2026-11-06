# Развёртывание GameHub на Ubuntu Server

Схема: **nginx** (HTTPS от Let's Encrypt, статика, обложки и аватары) → **gunicorn** (Django, сервис systemd)
→ **PostgreSQL** (база) + **Redis** (общий кеш). Проверено для Ubuntu 22.04 и 24.04.

```
Интернет ──443──> nginx ──unix-сокет──> gunicorn (Django) ──> PostgreSQL
                    │                                    └──> Redis
                    ├── /static/          → /srv/gamehub/static
                    ├── /media/covers|avatars → /srv/gamehub/media
                    └── /protected-media/ (internal) ← X-Accel-Redirect после проверки покупки
```

| Что | Где |
|---|---|
| Код | `/srv/gamehub/app` |
| Виртуальное окружение | `/srv/gamehub/venv` |
| Загруженные файлы (обложки, аватары, установщики) | `/srv/gamehub/media` |
| Собранная статика | `/srv/gamehub/static` |
| Настройки и секреты | `/etc/gamehub/gamehub.env` (640, root:gamehub) |
| Сервис | `gamehub.service` (пользователь `gamehub`) |
| Резервные копии | `/var/backups/gamehub` |

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
git archive --format=tar.gz -o gamehub.tar.gz HEAD
scp gamehub.tar.gz user@SERVER:/tmp/
```

```bash
sudo mkdir -p /srv/gamehub/app && sudo tar -xzf /tmp/gamehub.tar.gz -C /srv/gamehub/app
```

`git archive` берёт только закоммиченные файлы — сначала закоммитьте изменения.

## 3. Установка

Вариант А:

```bash
git clone https://github.com/you/gamehub.git /tmp/gamehub
sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com \
     REPO_URL=https://github.com/you/gamehub.git bash /tmp/gamehub/deploy/install.sh
```

Вариант Б:

```bash
sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com bash /srv/gamehub/app/deploy/install.sh
```

Добавьте `WWW=1`, если нужен ещё и `www.example.com`. Без `LETSENCRYPT_EMAIL` сайт поднимется по HTTP —
удобно для первой проверки; потом запустите скрипт ещё раз с e-mail.

Скрипт ставит пакеты, создаёт системного пользователя `gamehub`, базу PostgreSQL со случайным паролем,
`/etc/gamehub/gamehub.env` со случайным `DJANGO_SECRET_KEY`, применяет миграции, собирает статику,
запускает сервис, настраивает nginx и получает сертификат. Повторный запуск безопасен: пароли, база,
`.env` и nginx-конфиг с сертификатом не перезаписываются.

## 4. После установки

1. **Администратор** (демо-данные `seed_demo` на сервере не запускайте — у них известные пароли; команда
   и не запустится при `DJANGO_DEBUG=0`):

   ```bash
   sudo gamehub-manage createsuperuser
   ```

2. **Почта** — без неё не работают «Забыли пароль?» и уведомления формы связи. Впишите SMTP
   (своего почтового сервиса: Mailgun, SendGrid, Яндекс 360, Google Workspace…):

   ```bash
   sudo nano /etc/gamehub/gamehub.env     # EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
   sudo systemctl restart gamehub
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
sudo bash /srv/gamehub/app/deploy/update.sh            # git pull + зависимости + миграции + статика + перезапуск
```

Если код копируете архивом: распакуйте его поверх `/srv/gamehub/app` и запустите
`sudo NO_PULL=1 bash /srv/gamehub/app/deploy/update.sh`.

## 6. Резервные копии

```bash
sudo bash /srv/gamehub/app/deploy/backup.sh            # база + media + .env в /var/backups/gamehub
sudo crontab -e                                          # ежедневно в 03:30:
# 30 3 * * * /bin/bash /srv/gamehub/app/deploy/backup.sh >/var/log/gamehub-backup.log 2>&1
```

Копии старше 14 дней удаляются. Храните копии ещё и вне сервера (rsync, S3, облачный диск) — копия на том
же диске не спасёт при его потере. Команды восстановления — в конце `deploy/backup.sh`.

## 7. Диагностика

| Проблема | Что смотреть |
|---|---|
| 502 Bad Gateway | `sudo systemctl status gamehub`, `sudo journalctl -u gamehub -n 100` |
| 400 Bad Request | домен не в `DJANGO_ALLOWED_HOSTS` |
| 403 CSRF при отправке форм | адрес сайта не в `DJANGO_CSRF_TRUSTED_ORIGINS` (с `https://`) |
| Нет стилей | `sudo gamehub-manage collectstatic --noinput`, права на `/srv/gamehub/static` |
| Не скачиваются игры | файл есть в `/srv/gamehub/media/downloads`, `DJANGO_DOWNLOADS_ACCEL_PREFIX=/protected-media` |
| Ошибки nginx | `sudo nginx -t`, `sudo tail -f /var/log/nginx/error.log` |
| Не приходят письма | `sudo journalctl -u gamehub | grep -i smtp`, настройки SMTP |
| Сертификат | `sudo certbot renew --dry-run` (продление автоматическое, таймер certbot) |

## Безопасность — что уже сделано

- `DJANGO_DEBUG=0`, без `DJANGO_SECRET_KEY` сайт не запускается; `manage.py check --deploy` при установке.
- HTTPS-редирект, cookie только по HTTPS, HSTS, `X-Frame-Options: DENY`, `nosniff`.
- Установочные файлы платных игр недоступны по прямой ссылке: nginx отдаёт их только после проверки покупки
  в Django (`X-Accel-Redirect`). Напрямую открыты лишь обложки и аватары.
- gunicorn работает от отдельного пользователя без shell, с ограничениями systemd (запись только в `media`).
- Секреты — в `/etc/gamehub/gamehub.env`, не в коде и не в git.
