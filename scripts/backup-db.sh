#!/usr/bin/env sh
set -eu
mkdir -p backups
STAMP=$(date +"%Y-%m-%d_%H%M%S")
FILE="backups/sgv_epmvs_${STAMP}.sql.gz"
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-sgv_epmvs}" "${POSTGRES_DB:-sgv_epmvs}" | gzip > "$FILE"
echo "Backup creado: $FILE"
