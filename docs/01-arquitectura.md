# 01. Arquitectura Técnica

## 1. Contexto
- Sedes: central (120 equipos) y alterna (40 equipos).
- SO cliente: Windows y Debian (arranque dual).
- GLPI v11: sincronización de usuarios/equipos; autenticación la realiza LoginUV.
- Requisito crítico: respuesta de autenticación en máximo 5 segundos.

## 2. Componentes
1. Client Agent (Go)
- Servicio de sistema.
- UI de login con barra de progreso.
- Cola local SQLite para eventos offline.
- Heartbeat cada 30 s.

2. Server API (FastAPI)
- Autenticación y políticas de sesión.
- Gestión de usuarios/manual + CSV.
- Integración GLPI programada y manual.
- WebSocket para dashboard en vivo.

3. Admin Web (React)
- Monitoreo de equipos ocupados/libres.
- Gestión usuarios/equipos/salas.
- Reportes de uso y asistencia (PDF/XLSX).

4. Datos
- PostgreSQL: persistencia transaccional.
- Redis: presencia en tiempo real y pub/sub.

5. Nodo sede alterna (relay)
- API local de respaldo en sede alterna.
- Replica selectiva de usuarios/políticas.
- Reenvío de eventos a sede central al recuperar enlace.

## 3. Flujo de autenticación
1. Usuario ingresa credenciales en cliente.
2. Cliente inicia barra de progreso:
- 20% validación local.
- 45% conexión API.
- 70% validación credenciales.
- 90% políticas de sesión.
- 100% login exitoso.
3. Timeout 5 s al servidor central.
4. Si falla por enlace WAN, fallback automático a nodo relay local.
5. Cliente emite evento LOGIN_OK o LOGIN_FAIL.

## 4. Políticas de sesión
- `allow_multi_session=false`: máximo 1 sesión activa.
- `allow_multi_session=true`: máximo `max_sessions` activas.
- En logout/cierre/apagado inesperado se cierra sesión y se registra evento.

## 5. Observabilidad
- Logs estructurados por evento.
- Métricas mínimas: latencia auth, tasa de login_fail, heartbeat loss, equipos activos.
- Trazabilidad de cambios administrativos (auditoría normal).

## 6. Seguridad
- Contraseñas con Argon2id.
- JWT corto para cliente + refresh controlado.
- TLS interno y entre sedes.
- Firma HMAC de eventos cliente opcional para antifraude.
