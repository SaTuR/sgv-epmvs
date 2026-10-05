#!/usr/bin/env sh
set -eu
./scripts/backup-db.sh
STAMP=$(date +"%Y-%m-%d_%H%M%S")
tar -czf "backups/sgv_storage_${STAMP}.tar.gz" storage
echo "Backup de archivos creado."
