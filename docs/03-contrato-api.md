# 03. Contrato API Inicial

Base URL: `/api/v1`

## Auth
### POST `/auth/login`
Request:
```json
{
  "user_code": "20241234",
  "password": "secret",
  "hostname": "PC-021",
  "campus_code": "SEDE_ALT",
  "lab_code": "LAB-2"
}
```
Response 200:
```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "session": {
    "id": 1832,
    "user_code": "20241234",
    "full_name": "Ana Perez",
    "role": "student",
    "machine": "PC-021",
    "auth_mode": "central"
  }
}
```
Errors:
- `401 INVALID_CREDENTIALS`
- `409 SESSION_LIMIT_REACHED`
- `404 MACHINE_NOT_REGISTERED`
- `504 AUTH_TIMEOUT`

### POST `/auth/logout`
Request:
```json
{
  "session_id": 1832,
  "reason": "logout"
}
```
Response 204.

## Cliente
### POST `/client/heartbeat`
Request:
```json
{
  "hostname": "PC-021",
  "session_id": 1832,
  "os_type": "debian",
  "uptime_seconds": 10200,
  "timestamp": "2026-02-16T10:10:00Z"
}
```
Response 202.

### POST `/client/events/bulk`
Request:
```json
{
  "hostname": "PC-021",
  "events": [
    {
      "type": "UNEXPECTED_SHUTDOWN",
      "session_id": 1832,
      "timestamp": "2026-02-16T10:11:00Z",
      "payload": {"code": "kernel_panic"}
    }
  ]
}
```
Response 202.

## Usuarios
### POST `/users`
### GET `/users`
### PATCH `/users/{id}`
### POST `/users/import-csv`
Retorna resumen y errores por fila.

### GET `/users/import-csv`
Lista historial de importaciones CSV.

### GET `/users/import-csv/{import_id}`
Detalle de una importación con filas en error.

### GET `/users/import-csv/{import_id}/errors.csv`
Descarga las filas con error en formato CSV.

## GLPI
### POST `/integrations/glpi/sync`
Request:
```json
{"mode":"manual"}
```
Response:
```json
{"run_id": 90, "status": "processing"}
```

### GET `/integrations/glpi/sync`
Lista historial de ejecuciones de sincronización.

### GET `/integrations/glpi/sync/{run_id}`
Estado y resumen.

## Dashboard
### GET `/dashboard/summary?campus=SEDE_CENTRAL`
```json
{
  "connected_users": 71,
  "machines_occupied": 71,
  "machines_free": 49,
  "alerts": 2,
  "generated_at": "2026-02-16T10:30:00Z"
}
```

### GET `/dashboard/labs/{campus_code}/{lab_code}`
Listado de equipos y sesión activa.

### WS `/dashboard/ws`
Eventos: `machine_status_changed`, `session_started`, `session_ended`, `alert_raised`.

## Reportes
### GET `/reports/usage`
Filtros: `campus`, `lab`, `from`, `to`, `user_code`, `plan`, `semester`, `format=pdf|xlsx|json`.

### GET `/reports/attendance`
Filtros: `plan`, `semester`, `user_code`, `from`, `to`, `format=pdf|xlsx|json`.

## Convención de errores
```json
{
  "error": {
    "code": "SESSION_LIMIT_REACHED",
    "message": "User exceeded active sessions",
    "trace_id": "d8f8f3..."
  }
}
```
