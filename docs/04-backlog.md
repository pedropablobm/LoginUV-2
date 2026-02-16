# 04. Backlog Inicial (12 semanas)

## Fase 1 (Semanas 1-3): Core de autenticación y sesiones
1. API login/logout + JWT.
2. Regla de sesión única/múltiple.
3. Registro de máquinas y heartbeat.
4. Cliente Go con login y barra de progreso.
5. Dashboard resumen en vivo.

Criterios de aceptación:
- Login exitoso o fallo en <= 5s.
- Usuario sin multi-sesión no puede abrir segunda sesión.
- Estado de máquina cambia en tiempo real.

## Fase 2 (Semanas 4-5): Gestión de usuarios y CSV
1. CRUD usuarios.
2. Importación CSV con validación por filas.
3. Historial de importaciones y errores descargables.

Criterios:
- CSV de 1000 filas procesado con resumen consistente.
- Errores por fila visibles desde panel.

## Fase 3 (Semanas 6-7): Integración GLPI v11
1. Conector API GLPI (usuarios/equipos).
2. Sync manual y programado.
3. Reglas de reconciliación (upsert + inactivos).

Criterios:
- Sync completa con reporte de altas/actualizados/omitidos.
- Fallo de GLPI no bloquea autenticación local.

## Fase 4 (Semanas 8-9): Reportes
1. Reporte de uso de equipos.
2. Reporte de asistencia por plan/semestre/usuario.
3. Exportación PDF y XLSX.

Criterios:
- Reportes coinciden con sesiones almacenadas.
- Exportación en ambos formatos funcional.

## Fase 5 (Semanas 10-11): Resiliencia multi-sede
1. Nodo relay sede alterna.
2. Replicación de usuarios/políticas.
3. Reintento y reenvío de eventos offline.

Criterios:
- Con caída WAN, login sede alterna mantiene SLA local.
- Al restaurar WAN, eventos se sincronizan sin duplicados.

## Fase 6 (Semana 12): Piloto y cierre
1. Piloto 20 equipos.
2. Hardening de seguridad y métricas.
3. Runbook de operación.

Criterios:
- Incidencias críticas resueltas.
- Procedimiento operativo validado.
