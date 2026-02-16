# 05. Despliegue en Proxmox y Sede Alterna

## Objetivo
Desplegar LoginUV en dos sitios usando contenedores Docker:
- **Sitio central**: API + Web + PostgreSQL + Redis.
- **Sede alterna (relay)**: API local + PostgreSQL + Redis para continuidad.

## Topología recomendada
- `VM-CENTRAL` (Proxmox sitio principal):
  - `loginuv-api`
  - `loginuv-web`
  - `loginuv-postgres`
  - `loginuv-redis`
- `VM-RELAY` (Proxmox sede alterna):
  - `loginuv-relay-api`
  - `loginuv-relay-postgres`
  - `loginuv-relay-redis`

## Requisitos por VM
- Ubuntu Server 22.04+ (o Debian 12)
- Docker 24+
- Docker Compose v2
- Acceso a repo `LoginUV`

## 1) Despliegue sitio central
En `VM-CENTRAL`:

```bash
cd /opt
git clone <REPO_URL> LoginUV
cd LoginUV/infra
cp .env.central.example .env
# Editar secretos y credenciales
nano .env

docker compose --env-file .env -f docker-compose.yml up -d --build
```

Verificación:
```bash
docker compose -f docker-compose.yml ps
curl http://localhost:8000/api/v1/health
```

Puertos central:
- API: `8000`
- Web: `8080`
- PostgreSQL: `5432` (restringir por firewall)
- Redis: `6379` (restringir por firewall)

## 2) Despliegue sede alterna (relay)
En `VM-RELAY`:

```bash
cd /opt
git clone <REPO_URL> LoginUV
cd LoginUV/infra
cp .env.relay.example .env
# Editar secretos y credenciales
nano .env

docker compose --env-file .env -f docker-compose.relay.yml up -d --build
```

Verificación:
```bash
docker compose -f docker-compose.relay.yml ps
curl http://localhost:18000/api/v1/health
```

Puertos relay:
- API relay: `18000`
- PostgreSQL relay: `15432` (privado)
- Redis relay: `16379` (privado)

## 3) Reglas de red mínimas
- Clientes -> API central (`8000`) y API relay (`18000`).
- Panel admin -> Web central (`8080`).
- Bloquear acceso externo a PostgreSQL/Redis desde internet.
- Si hay VPN entre sedes, priorizar tráfico por VPN.

## 4) Variables GLPI
Configurar en `.env` del sitio central (y relay si aplica):
- `GLPI_BASE_URL`
- `GLPI_APP_TOKEN`
- `GLPI_USER_TOKEN`
- `GLPI_VERIFY_SSL`
- `GLPI_TIMEOUT_SECONDS`

## 5) Estrategia de continuidad
1. Cliente intenta autenticación central (timeout 5s).
2. Si falla, cliente intenta relay local.
3. Relay opera localmente hasta restaurar WAN.

## 6) Backup y recuperación
- Backup PostgreSQL cada 6 horas + backup full diario.
- Retención: 30 días.
- Prueba de restore mensual.

## 7) Monitoreo mínimo
- Uptime API central/relay.
- Latencia auth p95.
- Cantidad de sesiones activas.
- Error rate de sincronización GLPI.
