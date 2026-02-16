# 10. Creación de Clientes (Windows y Debian)

## Estado actual
El agente actual es una base funcional de consola. La integración como servicio (`systemd`/Windows Service) sigue pendiente.

## 1) Construir cliente Windows
En una máquina con Go 1.23+ y PowerShell:

```powershell
cd client-agent
powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1
```

Resultado:
- `client-agent/dist/windows/loginuv-agent.exe`

## 2) Construir cliente Debian/Linux
En una máquina Linux con Go 1.23+:

```bash
cd client-agent
bash ./scripts/build-debian.sh
```

Resultado:
- `client-agent/dist/linux/loginuv-agent`

## 3) Configuración base de cliente
Usar `client-agent/config/agent.example.json` como plantilla y ajustar:
- `api_base_url`: API central (ej. `http://10.10.0.10:8000`)
- `relay_base_url`: API de sede alterna (ej. `http://10.20.0.10:18000`)
- `campus_code`, `lab_code`, `hostname`

## 4) Instalación Windows (demo)

```powershell
cd client-agent
powershell -ExecutionPolicy Bypass -File .\deploy\windows\install-agent.ps1 `
  -BinaryPath .\dist\windows\loginuv-agent.exe `
  -ConfigPath .\config\agent.example.json
```

Archivos instalados en:
- `C:\ProgramData\LoginUV\loginuv-agent.exe`
- `C:\ProgramData\LoginUV\agent.json`

Ejecución manual:
```powershell
C:\ProgramData\LoginUV\loginuv-agent.exe
```

## 5) Instalación Debian (demo)

```bash
cd client-agent
bash ./deploy/linux/install-agent.sh ./dist/linux/loginuv-agent ./config/agent.example.json
```

Archivos instalados en:
- `/opt/loginuv/loginuv-agent`
- `/opt/loginuv/agent.json`

Ejecución manual:
```bash
/opt/loginuv/loginuv-agent
```

## 6) Validación mínima por cliente
1. Probar login con un usuario válido.
2. Confirmar respuesta de salud API:
   - central: `curl http://API_CENTRAL:8000/api/v1/health`
   - relay: `curl http://API_RELAY:18000/api/v1/health`
3. Verificar eventos en backend (`LOGIN_OK`, `HEARTBEAT`).

## 7) Escalamiento masivo (recomendado)
- Windows: despliegue por GPO/Intune/PDQ.
- Debian: Ansible + inventario por laboratorio.
- Mantener inventario con `hostname`, `campus_code`, `lab_code`.
