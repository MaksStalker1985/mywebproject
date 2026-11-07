#!/usr/bin/env bash
# Первичная установка TechVault на Ubuntu Server.
#
#   sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com bash deploy/install.sh
#
# Раскладка на сервере (совпадает с существующей конфигурацией nginx):
#   /var/www/django-site            — проект (manage.py), он же git-репозиторий
#   /var/www/django-site/venv       — виртуальное окружение
#   /var/www/django-site/media      — загруженные файлы, /var/www/django-site/staticfiles — статика
#   /run/django-site.sock           — сокет gunicorn (создаёт django-site.socket)
#   /etc/techvault/techvault.env    — настройки и секреты
#
# Переменные:
#   DOMAIN             — домен сайта (обязательно; DNS A-запись должна указывать на этот сервер)
#   WWW=1              — также обслуживать www.DOMAIN
#   LETSENCRYPT_EMAIL  — e-mail для Let's Encrypt; если не задан, HTTPS не настраивается
#   REPO_URL           — git-репозиторий; если не задан, код должен уже лежать в APP_DIR
#   BRANCH             — ветка (по умолчанию main)
#   APP_DIR            — каталог проекта (по умолчанию /var/www/django-site)
#   ADMIN_USERNAME     — логин администратора сайта (по умолчанию admin), ADMIN_EMAIL — его e-mail
#   SMTP_USER          — адрес почтового ящика для отправки писем (если не задан — спросит);
#                        support@DOMAIN — алиас, письма уходят от его имени
#
# Пароли (почтового ящика и администратора) скрипт спрашивает при запуске — не передавайте их
# в командной строке, чтобы они не попали в историю shell.
#
# Скрипт можно запускать повторно: пароли, база, .env и HTTPS-настройки nginx не перезаписываются.
set -euo pipefail

APP_USER=techvault
SITE=django-site                       # имя юнитов systemd и конфига nginx
APP_DIR=${APP_DIR:-/var/www/django-site}
VENV=$APP_DIR/venv
SOCKET=/run/$SITE.sock
ENV_DIR=/etc/techvault
ENV_FILE=$ENV_DIR/techvault.env
NGINX_CONF=/etc/nginx/sites-available/$SITE
BRANCH=${BRANCH:-main}
STAMP=$(date +%Y%m%d-%H%M%S)

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mОшибка: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "запустите через sudo"
[[ -n "${DOMAIN:-}" ]] || die "задайте DOMAIN, например: sudo DOMAIN=example.com bash deploy/install.sh"
grep -qi ubuntu /etc/os-release || echo "Внимание: скрипт проверялся для Ubuntu."

HOSTS=$DOMAIN
ORIGINS=https://$DOMAIN
CERT_DOMAINS=(-d "$DOMAIN")
if [[ "${WWW:-0}" == "1" ]]; then
    HOSTS="$HOSTS,www.$DOMAIN"
    ORIGINS="$ORIGINS,https://www.$DOMAIN"
    CERT_DOMAINS+=(-d "www.$DOMAIN")
fi

log "Проверка DNS"
LOCAL_IPS=" $(hostname -I) "
for ip in $(getent ahostsv4 "$DOMAIN" | awk '{print $1}' | sort -u); do
    [[ "$LOCAL_IPS" == *" $ip "* ]] || echo "Внимание: A-запись $DOMAIN → $ip, но у сервера другие адреса:$LOCAL_IPS"
done
for ip in $(getent ahostsv6 "$DOMAIN" 2>/dev/null | awk '{print $1}' | grep -v '^::ffff:' | sort -u); do
    [[ "$LOCAL_IPS" == *" $ip "* ]] || echo "Внимание: AAAA-запись $DOMAIN → $ip не принадлежит этому серверу — Let's Encrypt может не выдать сертификат. Исправьте или удалите AAAA-запись."
done

log "Пакеты"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q python3 python3-venv python3-dev git nginx postgresql redis-server gettext \
    certbot python3-certbot-nginx

log "Пользователь"
id -u $APP_USER >/dev/null 2>&1 || useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin $APP_USER

log "Код в $APP_DIR"
if [[ -d $APP_DIR/.git ]]; then
    if [[ -n "${REPO_URL:-}" ]]; then
        chown -R $APP_USER:www-data "$APP_DIR"
        sudo -u $APP_USER git -C "$APP_DIR" checkout -- locale
        sudo -u $APP_USER git -C "$APP_DIR" pull --ff-only
    fi
elif [[ -n "${REPO_URL:-}" ]]; then
    if [[ -d $APP_DIR && -n "$(ls -A "$APP_DIR")" ]]; then
        die "$APP_DIR уже существует и не пуст (это не git-репозиторий TechVault). Перенесите старый проект:
       sudo mv $APP_DIR $APP_DIR.old-$STAMP
и запустите скрипт снова."
    fi
    install -d -m 755 /var/www
    git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
[[ -f $APP_DIR/manage.py && -f $APP_DIR/deploy/django-site.socket ]] \
    || die "в $APP_DIR нет проекта TechVault — задайте REPO_URL или скопируйте проект туда"

install -d -o $APP_USER -g www-data -m 2750 "$APP_DIR/media" "$APP_DIR/media/covers" \
    "$APP_DIR/media/avatars" "$APP_DIR/media/downloads"
install -d -o $APP_USER -g www-data -m 2750 "$APP_DIR/staticfiles"
chown -R $APP_USER:www-data "$APP_DIR"
chmod 2750 "$APP_DIR"
chmod -R g+rX,o-rwx "$APP_DIR"

log "Виртуальное окружение и зависимости"
[[ -d $VENV ]] || sudo -u $APP_USER python3 -m venv "$VENV"
sudo -u $APP_USER "$VENV/bin/pip" install -q --upgrade pip
sudo -u $APP_USER "$VENV/bin/pip" install -q -r "$APP_DIR/requirements-prod.txt"

log "Файл настроек $ENV_FILE"
install -d -o root -g $APP_USER -m 750 $ENV_DIR
if [[ ! -f $ENV_FILE ]]; then
    SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    DB_PASS=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
    sed -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$SECRET|" \
        -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$DB_PASS|" \
        -e "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=$HOSTS|" \
        -e "s|^DJANGO_CSRF_TRUSTED_ORIGINS=.*|DJANGO_CSRF_TRUSTED_ORIGINS=$ORIGINS|" \
        -e "s|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=0|" \
        -e "s|/var/www/django-site|$APP_DIR|g" \
        -e "s|example\.com|$DOMAIN|g" \
        "$APP_DIR/deploy/techvault.env.example" > $ENV_FILE
    chown root:$APP_USER $ENV_FILE
    chmod 640 $ENV_FILE
    echo "Создан $ENV_FILE."
fi

# Почтовый ящик для отправки (SMTP). support@ — алиас, через него войти нельзя,
# поэтому спрашиваем адрес настоящего ящика (или берём из SMTP_USER=...).
if grep -q '^EMAIL_HOST_USER=$' $ENV_FILE; then
    if [[ -z "${SMTP_USER:-}" && -t 0 ]]; then
        echo "Письма будут уходить от support@$DOMAIN (алиас). Для входа в SMTP нужен настоящий почтовый ящик,"
        read -rp "к которому привязан алиас, например admin@$DOMAIN (Enter — пропустить): " SMTP_USER
    fi
    if [[ -n "${SMTP_USER:-}" ]]; then
        [[ "$SMTP_USER" =~ ^[^[:space:]\'\"|]+@[^[:space:]\'\"|]+$ ]] || die "некорректный адрес почтового ящика: $SMTP_USER"
        sed -i "s|^EMAIL_HOST_USER=$|EMAIL_HOST_USER=$SMTP_USER|" $ENV_FILE
    fi
fi
# Пароль почтового ящика (SMTP) — спрашиваем, если он ещё не задан
if grep -q '^EMAIL_HOST_PASSWORD=$' $ENV_FILE && ! grep -q '^EMAIL_HOST_USER=$' $ENV_FILE && [[ -t 0 ]]; then
    SMTP_USER=$(sed -n 's/^EMAIL_HOST_USER=//p' $ENV_FILE)
    read -rsp "Пароль почтового ящика $SMTP_USER (Enter — пропустить): " SMTP_PASS; echo
    if [[ -n "$SMTP_PASS" ]]; then
        [[ "$SMTP_PASS" != *"'"* ]] || die "пароль с апострофом (') не поддерживается в файле настроек"
        SMTP_PASS="$SMTP_PASS" python3 - "$ENV_FILE" <<'PY'
import os, sys
path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
pw = os.environ["SMTP_PASS"]
lines = [f"EMAIL_HOST_PASSWORD='{pw}'" if l == "EMAIL_HOST_PASSWORD=" else l for l in lines]
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
        unset SMTP_PASS
        echo "Пароль почты сохранён в $ENV_FILE (доступен только root и сервису)."
    fi
fi
# shellcheck disable=SC1090
set -a; . $ENV_FILE; set +a

log "PostgreSQL"
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER'" | grep -q 1; then
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE \"$POSTGRES_USER\" LOGIN PASSWORD '$POSTGRES_PASSWORD'"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" | grep -q 1; then
    sudo -u postgres createdb -O "$POSTGRES_USER" -E UTF8 "$POSTGRES_DB"
fi
systemctl enable --now redis-server postgresql

log "Команда techvault-manage (manage.py от имени сервиса)"
cat > /usr/local/bin/techvault-manage <<EOF
#!/bin/sh
# Запуск manage.py с настройками сервиса: sudo techvault-manage createsuperuser
exec sudo -u $APP_USER sh -c 'set -a; . $ENV_FILE; set +a; cd $APP_DIR && exec $VENV/bin/python manage.py "\$@"' sh "\$@"
EOF
chmod 755 /usr/local/bin/techvault-manage

log "Миграции и статика"
techvault-manage migrate --noinput
techvault-manage collectstatic --noinput -v 0
techvault-manage check --deploy --fail-level ERROR

log "Администратор сайта"
if [[ "$(techvault-manage shell -c 'from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())' 2>/dev/null | tail -1)" != "True" ]]; then
    if [[ -t 0 ]]; then
        echo "Создаём администратора. Придумайте надёжный пароль (его спросят дважды)."
        techvault-manage createsuperuser --username "${ADMIN_USERNAME:-admin}" --email "${ADMIN_EMAIL:-support@$DOMAIN}"
    else
        echo "Нет администратора — создайте: sudo techvault-manage createsuperuser"
    fi
else
    echo "Администратор уже есть."
fi

log "systemd: $SITE.socket + $SITE.service"
# Старые юниты, которые слушают тот же сокет (прежняя установка), останавливаем и сохраняем копию
for unit in /etc/systemd/system/*.socket /etc/systemd/system/*.service; do
    [[ -f $unit ]] || continue
    if grep -q "$SOCKET" "$unit" && ! grep -q "TechVault" "$unit"; then
        name=$(basename "$unit")
        echo "Отключаю прежний юнит $name (копия: $unit.bak-$STAMP)"
        systemctl disable --now "$name" 2>/dev/null || true
        mv "$unit" "$unit.bak-$STAMP"
    fi
done
for name in $SITE.service $SITE.socket; do
    unit=/etc/systemd/system/$name
    if [[ -f $unit ]] && ! grep -q "TechVault" "$unit"; then
        systemctl disable --now "$name" 2>/dev/null || true
        mv "$unit" "$unit.bak-$STAMP"
        echo "Прежний $name сохранён как $unit.bak-$STAMP"
    fi
done
sed -e "s|/var/www/django-site|$APP_DIR|g" "$APP_DIR/deploy/django-site.service" > /etc/systemd/system/$SITE.service
install -m 644 "$APP_DIR/deploy/django-site.socket" /etc/systemd/system/$SITE.socket
systemctl daemon-reload
systemctl enable --now $SITE.socket
systemctl enable $SITE.service
systemctl restart $SITE.service

log "nginx"
# Свой конфиг (с отметкой TechVault) не перезаписываем — в нём HTTPS-настройки certbot.
# Чужой (прежний) — сохраняем копию и заменяем: в нём вся папка media открыта для скачивания.
if [[ ! -f $NGINX_CONF ]] || ! grep -q "TechVault" $NGINX_CONF || [[ "${FORCE_NGINX:-0}" == "1" ]]; then
    [[ -f $NGINX_CONF ]] && cp $NGINX_CONF "$NGINX_CONF.bak-$STAMP" && echo "Прежний конфиг: $NGINX_CONF.bak-$STAMP"
    sed -e "s|server_name example.com;|server_name ${HOSTS//,/ };|" \
        -e "s|/var/www/django-site|$APP_DIR|g" \
        "$APP_DIR/deploy/nginx-django-site.conf" > $NGINX_CONF
fi
# Другие включённые сайты с этим же доменом отключаем (иначе nginx выберет не тот)
for f in /etc/nginx/sites-enabled/*; do
    [[ -e $f && "$(readlink -f "$f")" != "$NGINX_CONF" ]] || continue
    if grep -Eq "server_name[^;]*[[:space:]]$DOMAIN([[:space:];]|$)" "$f"; then
        echo "Отключаю сайт nginx $(basename "$f") — он обслуживает тот же домен"
        rm -f "$f"
    fi
done
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/$SITE
rm -f /etc/nginx/sites-enabled/default
install -m 644 "$APP_DIR/deploy/nginx-techvault-files.conf" /etc/nginx/conf.d/techvault-files.conf
nginx -t 2>/dev/null || rm -f /etc/nginx/conf.d/techvault-files.conf   # старый nginx без aio threads
nginx -t
systemctl reload nginx

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    ufw allow "Nginx Full" >/dev/null && echo "ufw: открыты порты 80 и 443"
fi

if [[ -n "${LETSENCRYPT_EMAIL:-}" ]]; then
    log "HTTPS (Let's Encrypt)"
    certbot --nginx "${CERT_DOMAINS[@]}" --redirect --agree-tos --non-interactive -m "$LETSENCRYPT_EMAIL"
    sed -i "s|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=1|" $ENV_FILE
    systemctl restart $SITE.service
else
    echo "LETSENCRYPT_EMAIL не задан — сайт работает по HTTP. Для HTTPS запустите скрипт ещё раз с LETSENCRYPT_EMAIL."
fi

log "Готово"
cat <<EOF
Сайт: http${LETSENCRYPT_EMAIL:+s}://$DOMAIN/

Дальше:
  1. Проверьте почту: войдите на сайт → «Забыли пароль?» или отправьте форму «Связь с производителем».
  2. Ключи платёжной системы:            sudo nano $ENV_FILE  →  sudo systemctl restart $SITE
  3. Журнал сервиса:                     sudo journalctl -u $SITE -f
  4. Обновление после изменений в коде:  sudo bash $APP_DIR/deploy/update.sh
EOF
