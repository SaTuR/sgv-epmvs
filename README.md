# Sistema de Gestión y Venta EPMVS

Sistema web para la Empresa Pública Municipal de Vivienda de Samborondón, orientado a la gestión de proyectos habitacionales, predios, clientes, reservas, ventas, cuotas, pagos, cartera, certificados y reportes.

Proyecto inicial: **San Joaquín**  
Etapas iniciales: **Etapa 1** y **Etapa 2**

## Stack

- React + TypeScript + Vite + Tailwind CSS
- FastAPI + Python
- PostgreSQL
- Alembic
- Nginx
- Docker Compose

## Inicio rápido

```bash
cp .env.example .env
docker compose up -d --build
```

Abrir:

- Sistema: http://localhost:8080
- API health: http://localhost:8080/api/health
- Swagger: http://localhost:8080/api/docs

## Producción

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Base de datos

```bash
docker compose exec backend alembic upgrade head
```

## Backups

```bash
./scripts/backup-db.sh
./scripts/backup-all.sh
```

Nunca subir `.env`, respaldos, documentos ciudadanos ni archivos de producción.
