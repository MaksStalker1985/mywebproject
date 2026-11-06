#!/usr/bin/env bash
# Резервная копия базы и загруженных файлов: sudo bash /srv/gamehub/app/deploy/backup.sh
# Ежедневно в 03:30 (sudo crontab -e):
#   30 3 * * * /bin/bash /srv/gamehub/app/deploy/backup.sh >/var/log/gamehub-backup.log 2>&1
# Копии хранятся KEEP_DAYS дней. Копируйте /var/backups/gamehub и на другой сервер или в облако.
set -euo pipefail

DEST=${DEST:-/var/backups/gamehub}
KEEP_DAYS=${KEEP_DAYS:-14}
STAMP=$(date +%Y%m%d-%H%M%S)

# shellcheck disable=SC1091
set -a; . /etc/gamehub/gamehub.env; set +a

install -d -m 700 "$DEST"
sudo -u postgres pg_dump --format=custom "$POSTGRES_DB" > "$DEST/db-$STAMP.dump"
tar -czf "$DEST/media-$STAMP.tar.gz" -C /srv/gamehub media
cp /etc/gamehub/gamehub.env "$DEST/env-$STAMP"
chmod 600 "$DEST"/*-"$STAMP"*

find "$DEST" -type f -mtime +"$KEEP_DAYS" -delete
echo "Готово: $DEST/*-$STAMP*"
# Восстановление базы:  sudo -u postgres pg_restore --clean --if-exists -d gamehub db-<дата>.dump
# Восстановление файлов: sudo tar -xzf media-<дата>.tar.gz -C /srv/gamehub
