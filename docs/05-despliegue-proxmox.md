# 05. Despliegue en Proxmox y Sede Alterna

## Topología recomendada
- VM1 (Proxmox central): `api + web + postgres + redis`.
- VM2 (Proxmox central opcional): réplica/backup DB.
- VM3 (sede alterna Linux): `relay + cache local + cola`.

## Requisitos
- Docker 24+
- Docker Compose v2
- Certificados TLS internos

## Puertos sugeridos
- API: 8000
- Web admin: 8080
- PostgreSQL: 5432 (solo red privada)
- Redis: 6379 (solo red privada)

## Estrategia de continuidad
1. Cliente intenta autenticación central (timeout 5s).
2. Si falla, intenta relay local sede alterna.
3. Relay registra eventos y reenvía cuando WAN vuelve.

## Backup y recuperación
- Backup PostgreSQL cada 6 horas + backup diario full.
- Retención: 30 días.
- Prueba de restore mensual.

## Monitoreo mínimo
- Uptime API y relay.
- Latencia auth p95.
- Cola offline pendiente.
- Error rate de sync GLPI.
