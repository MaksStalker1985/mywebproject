#!/usr/bin/env bash
# Первичная установка GameHub на Ubuntu Server 22.04 / 24.04.
#
#   sudo DOMAIN=example.com LETSENCRYPT_EMAIL=you@example.com bash deploy/install.sh
#
# Переменные:
#   DOMAIN             — домен сайта (обязательно; DNS A-запись должна указывать на этот сервер)
#   WWW=1              — также обслуживать www.DOMAIN
#   LETSENCRYPT_EMAIL  — e-mail для Let's Encrypt; если не задан, HTTPS не настраивается
#   REPO_URL           — git-репозиторий; если не задан, код должен уже лежать в /srv/gamehub/app
#   BRANCH             — ветка (по умолчанию main)
#
# Скрипт можно запускать повторно: существующие пароли, база и .env не перезаписываются.
set -euo pipefail

APP_USER=gamehub
BASE=/srv/gamehub
APP_DIR=$BASE/app
VENV=$BASE/venv
ENV_DIR=/etc/gamehub
ENV_FILE=$ENV_DIR/gamehub.env
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
        $APP_DIR/deploy/gamehub.env.example > $ENV_FILE
    chown root:$APP_USER $ENV_FILE
    chmod 640 $ENV_FILE
    echo "Создан $ENV_FILE — позже впишите в него SMTP и ключи платёжной системы."
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

log "Команда gamehub-manage (manage.py от имени сервиса)"
cat > /usr/local/bin/gamehub-manage <<'EOF'
#!/bin/sh
# Запуск manage.py с настройками сервиса: sudo gamehub-manage createsuperuser
exec sudo -u gamehub sh -c 'set -a; . /etc/gamehub/gamehub.env; set +a; cd /srv/gamehub/app && exec /srv/gamehub/venv/bin/python manage.py "$@"' sh "$@"
EOF
chmod 755 /usr/local/bin/gamehub-manage

log "Миграции и статика"
gamehub-manage compilemessages -v 0 || echo "compilemessages пропущен — используются готовые .mo"
gamehub-manage migrate --noinput
gamehub-manage collectstatic --noinput -v 0
gamehub-manage check --deploy --fail-level ERROR

log "systemd"
install -m 644 $APP_DIR/deploy/gamehub.service /etc/systemd/system/gamehub.service
systemctl daemon-reload
systemctl enable gamehub
systemctl restart gamehub

log "nginx"
# Существующий конфиг не трогаем: в нём HTTPS-настройки, добавленные certbot (FORCE_NGINX=1 — перезаписать)
if [[ ! -f /etc/nginx/sites-available/gamehub || "${FORCE_NGINX:-0}" == "1" ]]; then
    sed -e "s|server_name example.com;|server_name ${HOSTS//,/ };|" \
        $APP_DIR/deploy/nginx-gamehub.conf > /etc/nginx/sites-available/gamehub
fi
ln -sf /etc/nginx/sites-available/gamehub /etc/nginx/sites-enabled/gamehub
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [[ -n "${LETSENCRYPT_EMAIL:-}" ]]; then
    log "HTTPS (Let's Encrypt)"
    certbot --nginx "${CERT_DOMAINS[@]}" --redirect --agree-tos --non-interactive -m "$LETSENCRYPT_EMAIL"
    sed -i "s|^DJANGO_SECURE_SSL_REDIRECT=.*|DJANGO_SECURE_SSL_REDIRECT=1|" $ENV_FILE
    systemctl restart gamehub
else
    echo "LETSENCRYPT_EMAIL не задан — сайт работает по HTTP. Для HTTPS запустите скрипт ещё раз с LETSENCRYPT_EMAIL."
fi

log "Готово"
cat <<EOF
Сайт: http${LETSENCRYPT_EMAIL:+s}://$DOMAIN/

Дальше:
  1. Создайте администратора:            sudo gamehub-manage createsuperuser
  2. Впишите SMTP и ключи платежей в:    sudo nano $ENV_FILE  →  sudo systemctl restart gamehub
  3. Журнал сервиса:                     sudo journalctl -u gamehub -f
  4. Обновление после изменений в коде:  sudo bash $APP_DIR/deploy/update.sh
EOF
