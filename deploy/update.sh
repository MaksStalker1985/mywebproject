#!/usr/bin/env bash
# Обновление TechVault на сервере: sudo bash /srv/techvault/app/deploy/update.sh
# Если код копируется не через git, сначала скопируйте его в /srv/techvault/app и запустите с NO_PULL=1.
set -euo pipefail

APP_DIR=/srv/techvault/app
VENV=/srv/techvault/venv

[[ $EUID -eq 0 ]] || { echo "Запустите через sudo" >&2; exit 1; }

if [[ "${NO_PULL:-0}" != "1" && -d $APP_DIR/.git ]]; then
    echo "==> git pull"
    sudo -u techvault git -C $APP_DIR pull --ff-only
fi
chown -R techvault:www-data $APP_DIR
chmod -R g+rX,o-rwx $APP_DIR

echo "==> Зависимости"
sudo -u techvault $VENV/bin/pip install -q -r $APP_DIR/requirements-prod.txt

echo "==> Миграции и статика"
techvault-manage compilemessages -v 0 || true
techvault-manage migrate --noinput
techvault-manage collectstatic --noinput -v 0
techvault-manage check --deploy --fail-level ERROR

echo "==> Перезапуск"
install -m 644 $APP_DIR/deploy/techvault.service /etc/systemd/system/techvault.service
systemctl daemon-reload
systemctl restart techvault
systemctl --no-pager --lines=5 status techvault
