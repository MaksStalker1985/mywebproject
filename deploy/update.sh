#!/usr/bin/env bash
# Обновление GameHub на сервере: sudo bash /srv/gamehub/app/deploy/update.sh
# Если код копируется не через git, сначала скопируйте его в /srv/gamehub/app и запустите с NO_PULL=1.
set -euo pipefail

APP_DIR=/srv/gamehub/app
VENV=/srv/gamehub/venv

[[ $EUID -eq 0 ]] || { echo "Запустите через sudo" >&2; exit 1; }

if [[ "${NO_PULL:-0}" != "1" && -d $APP_DIR/.git ]]; then
    echo "==> git pull"
    sudo -u gamehub git -C $APP_DIR pull --ff-only
fi
chown -R gamehub:www-data $APP_DIR
chmod -R g+rX,o-rwx $APP_DIR

echo "==> Зависимости"
sudo -u gamehub $VENV/bin/pip install -q -r $APP_DIR/requirements-prod.txt

echo "==> Миграции и статика"
gamehub-manage compilemessages -v 0 || true
gamehub-manage migrate --noinput
gamehub-manage collectstatic --noinput -v 0
gamehub-manage check --deploy --fail-level ERROR

echo "==> Перезапуск"
install -m 644 $APP_DIR/deploy/gamehub.service /etc/systemd/system/gamehub.service
systemctl daemon-reload
systemctl restart gamehub
systemctl --no-pager --lines=5 status gamehub
