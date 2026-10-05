# Sistema de Gestión y Venta EPMVS

Sistema web para la Empresa Pública Municipal de Vivienda de Samborondón. Proyecto inicial: **San Joaquín**, Etapas **1 y 2**.

## Stack
React + TypeScript + Tailwind, FastAPI, PostgreSQL, Alembic, Nginx y Docker Compose.

## Identidad visual
Se utiliza el logo institucional EPM Vivienda Samborondón y la paleta base: verde oscuro `#3A6C32`, verde `#52AD56` y amarillo `#FAB71C`.

## Inicio rápido
```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.cli seed
```

Crear el administrador inicial:
```bash
docker compose exec backend python -m app.cli create-admin \
  --identification 0000000000 \
  --first-name Admin \
  --last-name EPMVS \
  --email admin@epmvs.local \
  --password 'CAMBIAR-CLAVE'
```

Abrir `http://localhost:8080`. Swagger: `http://localhost:8080/api/docs`.

Nunca subir `.env`, datos reales de ciudadanos, documentos, respaldos o secretos al repositorio.
