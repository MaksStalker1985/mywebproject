#!/usr/bin/env bash
# Первичная установка TechVault на Ubuntu Server 22.04 / 24.04.
#
#   sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com bash deploy/install.sh
#
# Переменные:
#   DOMAIN             — домен сайта (обязательно; DNS A-запись должна указывать на этот сервер)
#   WWW=1              — также обслуживать www.DOMAIN
#   LETSENCRYPT_EMAIL  — e-mail для Let's Encrypt; если не задан, HTTPS не настраивается
#   REPO_URL           — git-репозиторий; если не задан, код должен уже лежать в /srv/techvault/app
#   BRANCH             — ветка (по умолчанию main)
#   ADMIN_USERNAME     — логин администратора сайта (по умолчанию admin), ADMIN_EMAIL — его e-mail
#
# Пароли (почтового ящика и администратора) скрипт спрашивает при запуске — не передавайте их
# в командной строке, чтобы они не попали в историю shell.
#
# Скрипт можно запускать повторно: существующие пароли, база и .env не перезаписываются.
set -euo pipefail

APP_USER=techvault
BASE=/srv/techvault
APP_DIR=$BASE/app
VENV=$BASE/venv
ENV_DIR=/etc/techvault
ENV_FILE=$ENV_DIR/techvault.env
BRANCH=${BRANCH:-main}

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

log "Пользователь и каталоги"
id -u $APP_USER >/dev/null 2>&1 || useradd --system --home-dir $BASE --shell /usr/sbin/nologin $APP_USER
install -d -o $APP_USER -g www-data -m 2750 $BASE $BASE/media $BASE/media/covers $BASE/media/avatars $BASE/media/downloads
install -d -o $APP_USER -g www-data -m 2755 $BASE/static

log "Код"
if [[ -n "${REPO_URL:-}" ]]; then
    if [[ -d $APP_DIR/.git ]]; then
        sudo -u $APP_USER git -C $APP_DIR pull --ff-only
    else
        git clone --branch "$BRANCH" "$REPO_URL" $APP_DIR
    fi
fi
[[ -f $APP_DIR/manage.py ]] || die "нет $APP_DIR/manage.py — задайте REPO_URL или скопируйте проект в $APP_DIR"
chown -R $APP_USER:www-data $APP_DIR
chmod -R g+rX,o-rwx $APP_DIR

log "Виртуальное окружение и зависимости"
[[ -d $VENV ]] || sudo -u $APP_USER python3 -m venv $VENV
sudo -u $APP_USER $VENV/bin/pip install -q --upgrade pip
sudo -u $APP_USER $VENV/bin/pip install -q -r $APP_DIR/requirements-prod.txt

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
        -e "s|example\.com|$DOMAIN|g" \
        $APP_DIR/deploy/techvault.env.example > $ENV_FILE
    chown root:$APP_USER $ENV_FILE
    chmod 640 $ENV_FILE
    echo "Создан $ENV_FILE."
fi

# Пароль почтового ящика (SMTP) — спрашиваем, если он ещё не задан
if grep -q '^EMAIL_HOST_PASSWORD=$' $ENV_FILE && [[ -t 0 ]]; then
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
cat > /usr/local/bin/techvault-manage <<'EOF'
#!/bin/sh
# Запуск manage.py с настройками сервиса: sudo techvault-manage createsuperuser
exec sudo -u techvault sh -c 'set -a; . /etc/techvault/techvault.env; set +a; cd /srv/techvault/app && exec /srv/techvault/venv/bin/python manage.py "$@"' sh "$@"
EOF
chmod 755 /usr/local/bin/techvault-manage

log "Миграции и статика"
techvault-manage compilemessages -v 0 || echo "compilemessages пропущен — используются готовые .mo"
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

log "systemd"
install -m 644 $APP_DIR/deploy/techvault.service /etc/systemd/system/techvault.service
systemctl daemon-reload
systemctl enable techvault
systemctl restart techvault

log "nginx"
# Существующий конфиг не трогаем: в нём HTTPS-настройки, добавленные certbot (FORCE_NGINX=1 — перезаписать)
if [[ ! -f /etc/nginx/sites-available/techvault || "${FORCE_NGINX:-0}" == "1" ]]; then
    sed -e "s|server_name example.com;|server_name ${HOSTS//,/ };|" \
        $APP_DIR/deploy/nginx-techvault.conf > /etc/nginx/sites-available/techvault
fi
ln -sf /etc/nginx/sites-available/techvault /etc/nginx/sites-enabled/techvault
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    ufw allow "Nginx Full" >/dev/null && echo "ufw: открыты порты 80 и 443"
fi

if [[ -n "${LETSENCRYPT_EMAIL:-}" ]]; then
    log "HTTPS (Let's Encrypt)"
    certbot --nginx "${CERT_DOMAINS[@]}" --redirect --agree-tos --non-interactive -m "$LETSENCRYPT_EMAIL"
    sed -i "s|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=1|" $ENV_FILE
    systemctl restart techvault
else
    echo "LETSENCRYPT_EMAIL не задан — сайт работает по HTTP. Для HTTPS запустите скрипт ещё раз с LETSENCRYPT_EMAIL."
fi

log "Готово"
cat <<EOF
Сайт: http${LETSENCRYPT_EMAIL:+s}://$DOMAIN/

Дальше:
  1. Проверьте почту: войдите на сайт → «Забыли пароль?» или отправьте форму «Связь с производителем».
  2. Ключи платёжной системы:            sudo nano $ENV_FILE  →  sudo systemctl restart techvault
  3. Журнал сервиса:                     sudo journalctl -u techvault -f
  4. Обновление после изменений в коде:  sudo bash $APP_DIR/deploy/update.sh
EOF
