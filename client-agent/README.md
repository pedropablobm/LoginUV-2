# Client Agent (Go)

Base de agente multiplataforma para Windows/Debian.

## Ejecutar demo
```powershell
cd client-agent
go run ./cmd/agent
```

## Build Windows
```powershell
cd client-agent
powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1
```

## Build Debian/Linux
```bash
cd client-agent
bash ./scripts/build-debian.sh
```

## Instalación demo
- Windows: `deploy/windows/install-agent.ps1`
- Debian: `deploy/linux/install-agent.sh`
- Config template: `config/agent.example.json`

## Pendientes de implementación
- Integración real contra `/api/v1/auth/login`.
- Servicio del sistema (`systemd` y Windows Service).
- Cola SQLite offline + reintentos.
- Captura de eventos de apagado inesperado.
