# 08. OpenAPI Contract

## File
- `server/openapi.yaml`

## Scope
The contract includes endpoints for:
- Health
- Authentication (login/logout)
- Client heartbeat and events
- Dashboard summary and lab status
- Users and CSV import
- GLPI synchronization
- Usage and attendance reports

## Notes
- Base URL: `/api/v1`
- Error format standardized as:
```json
{
  "error": {
    "code": "SESSION_LIMIT_REACHED",
    "message": "User exceeded active sessions",
    "trace_id": "abc123"
  }
}
```
