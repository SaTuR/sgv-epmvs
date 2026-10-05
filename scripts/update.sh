#!/usr/bin/env sh
set -eu
./scripts/backup-all.sh
git pull origin main
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose ps
