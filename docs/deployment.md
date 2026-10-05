# Despliegue

Producción:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Configurar posteriormente dominio institucional, HTTPS y Certbot.
