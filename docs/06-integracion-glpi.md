# 06. Integración GLPI v11

## Objetivo
Usar GLPI como fuente de datos para usuarios y equipos, sin delegar autenticación.

## Alcance de sincronización
- Usuarios: código, nombre, correo, estado, rol base, plan/semestre si está disponible.
- Equipos: hostname, asset tag, sede/lab, estado de inventario.

## Modo de ejecución
1. Manual desde panel (`Sync now`).
2. Programado cada 30 minutos.

## Mapeo sugerido
- `glpi.user.id` -> `users.glpi_external_id`
- `glpi.computer.id` -> `machines.glpi_external_id`

## Reglas
- Upsert por `code` (usuarios) y `hostname` (equipos).
- No borrar físicamente; usar `is_active=false`.
- Registrar resumen de sync en `glpi_sync_runs`.

## Errores y resiliencia
- Si GLPI no responde: marcar run `failed`, no impactar login.
- Reintentos exponenciales: 3 intentos (5s, 15s, 30s).

## Seguridad
- Token API GLPI en variable de entorno.
- Acceso IP restringido entre servicios.
