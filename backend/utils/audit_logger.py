"""
Sistema de Auditoría y Logging - Registro de Eventos de Seguridad

Este módulo proporciona un sistema completo de auditoría para registrar,
almacenar y consultar eventos críticos del sistema. Es fundamental para:

- Cumplimiento normativo y regulatorio
- Análisis de seguridad y detección de amenazas
- Debugging y resolución de problemas
- Monitoreo de actividad de usuarios
- Trazabilidad de operaciones críticas

Funcionalidades principales:
- Registro automático de eventos con timestamps precisos
- Almacenamiento seguro en Firestore
- Consultas filtradas y paginadas
- Estadísticas y métricas de actividad
- Niveles de severidad para clasificación
- Retención y limpieza de logs antiguos

Tipos de eventos registrados:
- Autenticación (login, logout, fallos)
- Operaciones de documentos (upload, download, search)
- Cambios administrativos (roles, permisos)
- Errores del sistema y excepciones
- Eventos personalizados de aplicación

Estructura de eventos:
- timestamp: Momento exacto del evento
- user_id: Usuario que generó el evento (opcional)
- event_type: Categoría del evento
- details: Información contextual adicional
- severity: Nivel de importancia (INFO, WARNING, ERROR)
- source: Origen del evento (api, system, user)


"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import traceback

from firebase_admin import firestore
from services.firebase_service import get_firestore_client


# ==================================================================================
#                           CONFIGURACIÓN Y CONSTANTES
# ==================================================================================

# Colección de Firestore para almacenar logs de auditoría
AUDIT_COLLECTION = "audit_logs"

# Niveles de severidad disponibles
SEVERITY_LEVELS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4
}

# Límites de consulta para prevenir sobrecarga
MAX_QUERY_LIMIT = 10000
DEFAULT_QUERY_LIMIT = 100

# Configuración de retención de logs (días)
DEFAULT_RETENTION_DAYS = 365


# ==================================================================================
#                           FUNCIONES DE REGISTRO DE EVENTOS
# ==================================================================================

def log_event(
    user_id: Optional[str],
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
    source: str = "api"
) -> Optional[str]:
    """
    Registra un evento de auditoría en el sistema.
    
    Esta es la función principal para registrar eventos de auditoría.
    Almacena el evento en Firestore con toda la información contextual
    necesaria para análisis posterior.
    
    Args:
        user_id: ID del usuario que genera el evento (None para eventos del sistema)
        event_type: Tipo/categoría del evento (ej: "LOGIN", "DOCUMENT_UPLOAD")
        details: Información adicional sobre el evento
        severity: Nivel de severidad ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        source: Origen del evento ("api", "system", "user", "scheduler")
        
    Returns:
        Optional[str]: ID del documento creado en Firestore, None si falla
        
    Example:
        log_event(
            user_id="user123",
            event_type="DOCUMENT_UPLOAD",
            details={"filename": "contract.pdf", "size": 1024000},
            severity="INFO"
        )
    """
    try:
        # Validar y normalizar severidad
        severity = severity.upper()
        if severity not in SEVERITY_LEVELS:
            severity = "INFO"  # Fallback a INFO si no es válida
        
        # Preparar datos del evento
        event_data = {
            "timestamp": firestore.SERVER_TIMESTAMP,  # Timestamp del servidor Firestore
            "user_id": user_id,
            "event_type": event_type.upper(),  # Normalizar a mayúsculas
            "details": details or {},
            "severity": severity,
            "severity_level": SEVERITY_LEVELS[severity],  # Para consultas numéricas
            "source": source,
            "created_at": datetime.now().isoformat() + "Z",  # Timestamp local adicional
        }
        
        # Enriquecer con información del contexto si está disponible
        if details:
            # Añadir información adicional si no está presente
            if "timestamp_iso" not in details:
                event_data["details"]["timestamp_iso"] = datetime.now().isoformat() + "Z"
        
        # Almacenar en Firestore
        firestore_client = get_firestore_client()
        doc_ref = firestore_client.collection(AUDIT_COLLECTION).add(event_data)
        
        # Devolver ID del documento creado
        return doc_ref[1].id if doc_ref and doc_ref[1] else None
        
    except Exception as e:
        # Manejar errores de logging sin fallar la operación principal
        # Mensajes de depuración - comentados para producción
        # print(f"❌ Error registrando evento de auditoría: {e}")
        # print(f"   Evento: {event_type}, Usuario: {user_id}")
        
        # Intentar registrar el error de logging como último recurso
        try:
            error_event = {
                "timestamp": firestore.SERVER_TIMESTAMP,
                "user_id": "system",
                "event_type": "AUDIT_LOG_ERROR",
                "details": {
                    "original_event_type": event_type,
                    "original_user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                "severity": "ERROR",
                "severity_level": SEVERITY_LEVELS["ERROR"],
                "source": "audit_system"
            }
            
            firestore_client = get_firestore_client()
            firestore_client.collection(AUDIT_COLLECTION).add(error_event)
            
        except:
            # Si esto también falla, no hay mucho más que hacer
            # print("❌❌ Error crítico: No se pudo registrar ni el evento original ni el error")
            pass
        
        return None


def log_system_event(event_type: str, details: Optional[Dict[str, Any]] = None, severity: str = "INFO") -> Optional[str]:
    """
    Registra un evento del sistema (sin usuario específico).
    
    Función de conveniencia para registrar eventos generados automáticamente
    por el sistema, como inicializaciones, tareas programadas, etc.
    
    Args:
        event_type: Tipo del evento del sistema
        details: Información adicional del evento
        severity: Nivel de severidad del evento
        
    Returns:
        Optional[str]: ID del evento registrado
    """
    return log_event(
        user_id=None,
        event_type=event_type,
        details=details,
        severity=severity,
        source="system"
    )


def log_error(
    error: Exception,
    context: str,
    user_id: Optional[str] = None,
    additional_details: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Registra un error con información detallada para debugging.
    
    Captura información completa del error incluyendo stack trace
    y contexto para facilitar la resolución de problemas.
    
    Args:
        error: Excepción que se produjo
        context: Contexto donde ocurrió el error
        user_id: Usuario afectado (si aplica)
        additional_details: Información adicional sobre el error
        
    Returns:
        Optional[str]: ID del evento de error registrado
    """
    error_details = {
        "error_message": str(error),
        "error_type": type(error).__name__,
        "context": context,
        "stack_trace": traceback.format_exc(),
        **(additional_details or {})
    }
    
    return log_event(
        user_id=user_id,
        event_type="SYSTEM_ERROR",
        details=error_details,
        severity="ERROR",
        source="system"
    )


# ==================================================================================
#                           FUNCIONES DE CONSULTA DE LOGS
# ==================================================================================

def fetch_logs(
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Obtiene logs de auditoría con filtros y paginación.
    
    Función principal para consultar logs con capacidades avanzadas
    de filtrado, ordenamiento y paginación.
    
    Args:
        limit: Número máximo de logs a devolver
        offset: Número de logs a omitir (para paginación)
        filters: Diccionario con filtros a aplicar
                - event_type: Filtrar por tipo de evento
                - user_id: Filtrar por usuario específico
                - severity: Filtrar por nivel de severidad
                - start_date: Fecha de inicio (ISO format)
                - end_date: Fecha de fin (ISO format)
                - source: Filtrar por origen del evento
        
    Returns:
        Dict[str, Any]: Diccionario con logs y metadatos de consulta
        
    Example:
        logs = fetch_logs(
            limit=50,
            filters={
                "event_type": "LOGIN",
                "severity": "INFO",
                "start_date": "2024-01-01T00:00:00Z"
            }
        )
    """
    try:
        # Validar límite
        if limit > MAX_QUERY_LIMIT:
            limit = MAX_QUERY_LIMIT
        
        # Obtener cliente de Firestore
        firestore_client = get_firestore_client()
        
        # Construir consulta base
        query = firestore_client.collection(AUDIT_COLLECTION)
        
        # Aplicar filtros si se proporcionan
        if filters:
            # Filtro por tipo de evento
            if "event_type" in filters and filters["event_type"]:
                query = query.where("event_type", "==", filters["event_type"].upper())
            
            # Filtro por usuario
            if "user_id" in filters and filters["user_id"]:
                query = query.where("user_id", "==", filters["user_id"])
            
            # Filtro por severidad
            if "severity" in filters and filters["severity"]:
                severity_upper = filters["severity"].upper()
                if severity_upper in SEVERITY_LEVELS:
                    query = query.where("severity", "==", severity_upper)
            
            # Filtro por origen
            if "source" in filters and filters["source"]:
                query = query.where("source", "==", filters["source"])
            
            # Filtros de fecha (limitados por capacidades de Firestore)
            if "start_date" in filters and filters["start_date"]:
                try:
                    start_dt = datetime.fromisoformat(filters["start_date"].replace('Z', '+00:00'))
                    query = query.where("timestamp", ">=", start_dt)
                except ValueError:
                    pass  # Ignorar fechas mal formateadas
            
            if "end_date" in filters and filters["end_date"]:
                try:
                    end_dt = datetime.fromisoformat(filters["end_date"].replace('Z', '+00:00'))
                    query = query.where("timestamp", "<=", end_dt)
                except ValueError:
                    pass  # Ignorar fechas mal formateadas
        
        # Ordenar por timestamp descendente (más recientes primero)
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)
        
        # Aplicar límite
        query = query.limit(limit + offset)  # Obtener más para manejar offset
        
        # Ejecutar consulta
        docs = list(query.stream())
        
        # Aplicar offset manualmente (Firestore no tiene offset nativo eficiente)
        docs = docs[offset:offset + limit]
        
        # Convertir documentos a diccionarios
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data["id"] = doc.id
            
            # Convertir timestamp de Firestore a string ISO
            if "timestamp" in log_data and log_data["timestamp"]:
                if hasattr(log_data["timestamp"], "timestamp"):
                    # Es un timestamp de Firestore
                    log_data["timestamp"] = datetime.fromtimestamp(
                        log_data["timestamp"].timestamp()
                    ).isoformat() + "Z"
            
            logs.append(log_data)
        
        # Contar total de documentos (aproximado)
        total_count = len(docs) + offset  # Estimación
        
        return {
            "logs": logs,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "filters_applied": filters or {},
            "query_timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        # Registrar error de consulta (si es posible)
        try:
            log_error(e, "fetch_logs", additional_details={
                "limit": limit,
                "offset": offset,
                "filters": filters
            })
        except:
            pass
        
        # Devolver estructura vacía en caso de error
        return {
            "logs": [],
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "filters_applied": filters or {},
            "error": str(e),
            "query_timestamp": datetime.now().isoformat() + "Z"
        }


def get_recent_logs(limit: int = DEFAULT_QUERY_LIMIT) -> List[Dict[str, Any]]:
    """
    Obtiene los logs más recientes (función de conveniencia).
    
    Args:
        limit: Número de logs recientes a obtener
        
    Returns:
        List[Dict[str, Any]]: Lista de logs recientes
    """
    result = fetch_logs(limit=limit)
    return result.get("logs", [])


def get_logs_by_user(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Obtiene logs específicos de un usuario.
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de logs
        
    Returns:
        List[Dict[str, Any]]: Logs del usuario especificado
    """
    result = fetch_logs(
        limit=limit,
        filters={"user_id": user_id}
    )
    return result.get("logs", [])


def get_logs_by_event_type(event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Obtiene logs de un tipo específico de evento.
    
    Args:
        event_type: Tipo de evento a buscar
        limit: Número máximo de logs
        
    Returns:
        List[Dict[str, Any]]: Logs del tipo de evento especificado
    """
    result = fetch_logs(
        limit=limit,
        filters={"event_type": event_type}
    )
    return result.get("logs", [])


# ==================================================================================
#                           FUNCIONES DE ESTADÍSTICAS Y ANÁLISIS
# ==================================================================================

def get_audit_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula estadísticas de auditoría para un período.
    
    Proporciona métricas útiles sobre la actividad del sistema
    basadas en los logs de auditoría del período especificado.
    
    Args:
        start_date: Fecha de inicio en formato ISO
        end_date: Fecha de fin en formato ISO
        
    Returns:
        Dict[str, Any]: Estadísticas calculadas
    """
    try:
        # Configurar fechas por defecto (últimos 30 días)
        if not end_date:
            end_date = datetime.now().isoformat() + "Z"
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat() + "Z"
        
        # Obtener logs del período
        logs_data = fetch_logs(
            limit=MAX_QUERY_LIMIT,
            filters={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        logs = logs_data.get("logs", [])
        
        # Calcular estadísticas
        stats = {
            "total_events": len(logs),
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "events_by_type": {},
            "events_by_severity": {},
            "events_by_user": {},
            "events_by_source": {},
            "events_by_day": {},
            "unique_users": set(),
            "error_rate": 0.0
        }
        
        error_count = 0
        
        # Procesar cada log
        for log in logs:
            # Contar por tipo
            event_type = log.get("event_type", "UNKNOWN")
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            
            # Contar por severidad
            severity = log.get("severity", "INFO")
            stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1
            
            if severity in ["ERROR", "CRITICAL"]:
                error_count += 1
            
            # Contar por usuario
            user_id = log.get("user_id")
            if user_id:
                stats["events_by_user"][user_id] = stats["events_by_user"].get(user_id, 0) + 1
                stats["unique_users"].add(user_id)
            
            # Contar por origen
            source = log.get("source", "unknown")
            stats["events_by_source"][source] = stats["events_by_source"].get(source, 0) + 1
            
            # Contar por día
            timestamp = log.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        day = timestamp[:10]  # Tomar solo YYYY-MM-DD
                        stats["events_by_day"][day] = stats["events_by_day"].get(day, 0) + 1
                except:
                    pass
        
        # Calcular métricas derivadas
        stats["unique_users"] = len(stats["unique_users"])
        stats["error_rate"] = (error_count / len(logs) * 100) if logs else 0
        
        # Ordenar diccionarios por frecuencia
        stats["events_by_type"] = dict(sorted(
            stats["events_by_type"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        stats["events_by_user"] = dict(sorted(
            stats["events_by_user"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return stats
        
    except Exception as e:
        # Registrar error de estadísticas
        try:
            log_error(e, "get_audit_statistics", additional_details={
                "start_date": start_date,
                "end_date": end_date
            })
        except:
            pass
        
        # Devolver estadísticas vacías
        return {
            "total_events": 0,
            "error": str(e),
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }


# ==================================================================================
#                           FUNCIONES DE MANTENIMIENTO
# ==================================================================================

def cleanup_old_logs(days_to_keep: int = DEFAULT_RETENTION_DAYS) -> Dict[str, Any]:
    """
    Limpia logs de auditoría más antiguos que el período especificado.
    
    ⚠️ IMPORTANTE: Esta operación elimina datos permanentemente.
    Debe usarse con precaución y después de crear backups si es necesario.
    
    Args:
        days_to_keep: Número de días de logs a mantener
        
    Returns:
        Dict[str, Any]: Resultado de la operación de limpieza
    """
    try:
        # Calcular fecha límite
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Registrar intento de limpieza
        log_system_event(
            "AUDIT_CLEANUP_STARTED",
            details={
                "cutoff_date": cutoff_date.isoformat(),
                "days_to_keep": days_to_keep
            },
            severity="WARNING"
        )
        
        # Obtener cliente de Firestore
        firestore_client = get_firestore_client()
        
        # Buscar logs antiguos
        old_logs_query = (
            firestore_client.collection(AUDIT_COLLECTION)
            .where("timestamp", "<", cutoff_date)
            .limit(1000)  # Procesar en lotes para evitar timeouts
        )
        
        # Contar y eliminar logs antiguos
        deleted_count = 0
        batch = firestore_client.batch()
        batch_size = 0
        
        for doc in old_logs_query.stream():
            batch.delete(doc.reference)
            batch_size += 1
            deleted_count += 1
            
            # Ejecutar lote cuando alcance el límite
            if batch_size >= 500:  # Límite de Firestore para batches
                batch.commit()
                batch = firestore_client.batch()
                batch_size = 0
        
        # Ejecutar lote final si tiene elementos
        if batch_size > 0:
            batch.commit()
        
        # Registrar resultado
        result = {
            "deleted_logs": deleted_count,
            "cutoff_date": cutoff_date.isoformat() + "Z",
            "days_kept": days_to_keep,
            "status": "completed"
        }
        
        log_system_event(
            "AUDIT_CLEANUP_COMPLETED",
            details=result,
            severity="WARNING"
        )
        
        return result
        
    except Exception as e:
        # Registrar fallo de limpieza
        error_result = {
            "deleted_logs": 0,
            "error": str(e),
            "days_to_keep": days_to_keep,
            "status": "failed"
        }
        
        try:
            log_error(e, "cleanup_old_logs", additional_details=error_result)
        except:
            pass
        
        return error_result


# ==================================================================================
#                           FUNCIONES DE UTILIDAD
# ==================================================================================

def validate_event_type(event_type: str) -> bool:
    """
    Valida si un tipo de evento es válido.
    
    Args:
        event_type: Tipo de evento a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    # Lista de tipos de eventos válidos (expandible)
    valid_types = {
        "LOGIN", "LOGOUT", "LOGIN_FAILED",
        "DOCUMENT_UPLOAD", "DOCUMENT_DOWNLOAD", "DOCUMENT_SEARCH",
        "USER_REGISTERED", "USER_PROMOTED_TO_ADMIN",
        "SYSTEM_ERROR", "AUDIT_LOG_ERROR",
        "SYSTEM_STARTUP", "SYSTEM_SHUTDOWN"
    }
    
    return event_type.upper() in valid_types


def format_log_for_display(log: Dict[str, Any]) -> str:
    """
    Formatea un log para visualización legible.
    
    Args:
        log: Diccionario con datos del log
        
    Returns:
        str: Log formateado para mostrar
    """
    timestamp = log.get("timestamp", "Unknown")
    user_id = log.get("user_id", "System")
    event_type = log.get("event_type", "UNKNOWN")
    severity = log.get("severity", "INFO")
    
    return f"[{timestamp}] {severity} - {event_type} (User: {user_id})"


# ==================================================================================
#                           EVENTOS DE INICIO DEL SISTEMA
# ==================================================================================

def initialize_audit_system() -> None:
    """
    Inicializa el sistema de auditoría registrando el evento de startup.
    """
    log_system_event(
        "AUDIT_SYSTEM_INITIALIZED",
        details={
            "audit_collection": AUDIT_COLLECTION,
            "retention_days": DEFAULT_RETENTION_DAYS,
            "max_query_limit": MAX_QUERY_LIMIT
        },
        severity="INFO"
    )


# Inicializar sistema al importar el módulo
# initialize_audit_system()  # Comentado para evitar logs en cada import
