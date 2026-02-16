# Client Agent (Go)

Base de agente multiplataforma para Windows/Debian.

## Ejecutar demo
```powershell
cd client-agent
go run ./cmd/agent
```

## Pendientes de implementación
- Integración real contra `/api/v1/auth/login`.
- Servicio del sistema (`systemd` y Windows Service).
- Cola SQLite offline + reintentos.
- Captura de eventos de apagado inesperado.
