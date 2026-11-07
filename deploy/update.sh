#!/usr/bin/env bash
# Обновление TechVault на сервере: sudo bash /var/www/django-site/deploy/update.sh
# Если код копируется не через git, сначала скопируйте его в каталог проекта и запустите с NO_PULL=1.
set -euo pipefail

APP_DIR=${APP_DIR:-/var/www/django-site}
VENV=$APP_DIR/venv
SITE=django-site

[[ $EUID -eq 0 ]] || { echo "Запустите через sudo" >&2; exit 1; }

chown -R techvault:www-data "$APP_DIR"
if [[ "${NO_PULL:-0}" != "1" && -d $APP_DIR/.git ]]; then
    echo "==> git pull"
    # Готовые .mo лежат в репозитории; старые версии скрипта пересобирали их на сервере,
    # из-за чего git pull отказывался обновлять. Возвращаем их к версии из git.
    sudo -u techvault git -C "$APP_DIR" checkout -- locale
    sudo -u techvault git -C "$APP_DIR" pull --ff-only
fi
chmod -R g+rX,o-rwx "$APP_DIR"

echo "==> Зависимости"
sudo -u techvault "$VENV/bin/pip" install -q -r "$APP_DIR/requirements-prod.txt"

echo "==> Миграции и статика"
techvault-manage migrate --noinput
techvault-manage collectstatic --noinput -v 0
techvault-manage check --deploy --fail-level ERROR

echo "==> nginx: отдача больших файлов"
install -m 644 "$APP_DIR/deploy/nginx-techvault-files.conf" /etc/nginx/conf.d/techvault-files.conf
if nginx -t 2>/dev/null; then
    systemctl reload nginx
else
    echo "nginx -t не прошёл с techvault-files.conf — файл убран, конфигурация не изменена" >&2
    rm -f /etc/nginx/conf.d/techvault-files.conf
fi

echo "==> Перезапуск"
sed -e "s|/var/www/django-site|$APP_DIR|g" "$APP_DIR/deploy/django-site.service" > /etc/systemd/system/$SITE.service
install -m 644 "$APP_DIR/deploy/django-site.socket" /etc/systemd/system/$SITE.socket
systemctl daemon-reload
systemctl restart $SITE.service
systemctl --no-pager --lines=5 status $SITE.service
