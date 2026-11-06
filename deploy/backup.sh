#!/usr/bin/env bash
# Резервная копия базы и загруженных файлов: sudo bash /var/www/django-site/deploy/backup.sh
# Ежедневно в 03:30 (sudo crontab -e):
#   30 3 * * * /bin/bash /var/www/django-site/deploy/backup.sh >/var/log/techvault-backup.log 2>&1
# Копии хранятся KEEP_DAYS дней. Копируйте /var/backups/techvault и на другой сервер или в облако.
set -euo pipefail

DEST=${DEST:-/var/backups/techvault}
KEEP_DAYS=${KEEP_DAYS:-14}
STAMP=$(date +%Y%m%d-%H%M%S)

# shellcheck disable=SC1091
set -a; . /etc/techvault/techvault.env; set +a

install -d -m 700 "$DEST"
sudo -u postgres pg_dump --format=custom "$POSTGRES_DB" > "$DEST/db-$STAMP.dump"
tar -czf "$DEST/media-$STAMP.tar.gz" -C /var/www/django-site media
cp /etc/techvault/techvault.env "$DEST/env-$STAMP"
chmod 600 "$DEST"/*-"$STAMP"*

find "$DEST" -type f -mtime +"$KEEP_DAYS" -delete
echo "Готово: $DEST/*-$STAMP*"
# Восстановление базы:  sudo -u postgres pg_restore --clean --if-exists -d techvault db-<дата>.dump
# Восстановление файлов: sudo tar -xzf media-<дата>.tar.gz -C /var/www/django-site
