#!/usr/bin/env sh
set -eu
if [ $# -ne 1 ]; then
  echo "Uso: $0 backups/archivo.sql.gz"
  exit 1
fi
gzip -dc "$1" | docker compose exec -T db psql -U "${POSTGRES_USER:-sgv_epmvs}" "${POSTGRES_DB:-sgv_epmvs}"
echo "Restauración terminada."
