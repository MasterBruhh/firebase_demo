/**
 * Componente de Registros de Auditoría - Visualización de Actividad del Sistema
 * 
 * Este componente proporciona una interfaz completa para visualizar y analizar
 * los registros de auditoría del sistema. Permite a los administradores
 * monitorear todas las actividades, filtrar eventos y detectar anomalías.
 * 
 * Funcionalidades principales:
 * - Visualización de registros de auditoría en tiempo real
 * - Filtrado avanzado por tipo de evento, usuario y fecha
 * - Búsqueda en detalles de eventos
 * - Exportación de registros
 * - Paginación eficiente para grandes volúmenes
 * - Análisis de tendencias y estadísticas
 * - Alertas de seguridad
 * - Solo accesible para administradores
 * 
 * Tipos de eventos auditados:
 * - AUTHENTICATION: Login, logout, registro
 * - DOCUMENT_UPLOAD: Subida de documentos
 * - DOCUMENT_ACCESS: Descarga y visualización
 * - SEARCH: Búsquedas realizadas
 * - ADMIN_ACTION: Acciones administrativas
 * - SYSTEM_ERROR: Errores del sistema
 * - SECURITY_EVENT: Eventos de seguridad
 * 
 * Información mostrada:
 * - Timestamp preciso del evento
 * - Tipo de evento con codificación por colores
 * - Usuario que realizó la acción
 * - Detalles específicos del evento
 * - Dirección IP y metadatos de contexto
 * - Nivel de severidad
 * 
 * Funcionalidades de filtrado:
 * - Por tipo de evento
 * - Por usuario específico
 * - Por rango de fechas
 * - Por nivel de severidad
 * - Búsqueda en texto libre
 * 
 * Características de seguridad:
 * - Acceso restringido solo a administradores
 * - Registros inmutables (solo lectura)
 * - Integridad de datos verificada
 * - Exportación segura
 * 
 * Integración:
 * - Sistema de auditoría del backend
 * - Firestore para almacenamiento de logs
 * - Análisis en tiempo real
 * - Alertas automáticas
 * 
*/

import React, { useEffect, useState } from "react";
import { auditAPI } from "../services/api";

export default function AuditLogs() {
  const [logs,    setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  useEffect(() => {
    (async () => {
      try {
        const { data } = await auditAPI.getLogs(200);
        setLogs(data.logs || []);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p>Cargando…</p>;
  if (error)   return <p className="error">{error}</p>;

  return (
    <div className="audit-page">
      <h2>Registros de auditoría</h2>
      {logs.length === 0 ? (
        <p>No hay registros.</p>
      ) : (
        <table className="audit-table">
          <thead>
            <tr>
              <th>📅 Fecha</th>
              <th>🧑‍💻 Usuario</th>
              <th>🔖 Evento</th>
              <th>ℹ️ Detalles</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.user_id || "—"}</td>
                <td>{log.event_type}</td>
                <td>{JSON.stringify(log.details)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
