# LoginUV

Sistema cliente-servidor para control de acceso y uso de computadores en salas de sistemas universitarias.

## Objetivo
LoginUV permite autenticación de estudiantes/docentes en equipos Windows y Debian, monitoreo en tiempo real, gestión de usuarios, sincronización con GLPI v11 y generación de reportes de uso/asistencia.

## Arquitectura propuesta
- `client-agent/`: agente multiplataforma en Go (Windows Service / systemd), login local, heartbeat y cola offline.
- `server/`: API central en FastAPI, reglas de sesión, reportes, importación CSV, integración GLPI.
- `admin-web/`: panel administrativo web (React + Vite).
- `infra/`: despliegue base con Docker Compose (PostgreSQL, Redis, API, Web).
- `docs/`: diseño técnico para iniciar implementación.

## Entregables listos
1. Arquitectura técnica y flujo de autenticación.
2. Modelo de datos SQL inicial.
3. Contrato de API (endpoints, payloads, errores).
4. OpenAPI (`server/openapi.yaml`).
5. Migraciones Alembic iniciales.
6. Backlog por fases con criterios de aceptación.
7. Guía de despliegue en Proxmox y sede alterna.
8. Estrategia de sincronización con GLPI v11.

## Inicio rápido
```powershell
cd infra
copy .env.example .env
docker compose up -d --build
```

Despliegue por sitio en Proxmox:
- Sitio central: `infra/docker-compose.yml` + `infra/.env.central.example`
- Sede alterna (relay): `infra/docker-compose.relay.yml` + `infra/.env.relay.example`
- Guía: `docs/05-despliegue-proxmox.md`

Servicios esperados:
- API: `http://localhost:8000`
- Web admin: `http://localhost:5173` (modo dev) o `http://localhost:8080` (contenedor)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Flujo funcional clave
1. Usuario inicia sesión desde cliente.
2. Cliente muestra progreso de autenticación (20/45/70/90/100).
3. API valida credenciales y regla de sesiones (single/multi equipo).
4. Cliente reporta heartbeat cada 30 segundos.
5. Dashboard muestra ocupados/libres en tiempo real.
6. Reportes exportables en PDF y Excel.

## Estructura del repositorio
```text
LoginUV/
  admin-web/
  client-agent/
  docs/
  infra/
  server/
```

Guía de clientes:
- `docs/10-clientes.md`

## Próximos pasos sugeridos
1. Completar autenticación con hash Argon2 y JWT.
2. Implementar importador CSV y sincronización GLPI.
3. Implementar reportes PDF/XLSX.
4. Desplegar nodo relay en sede alterna para continuidad.

