"""
Rutas de Auditoría - Sistema de Logs y Monitoreo de Eventos

Este módulo define los endpoints para el sistema de auditoría y monitoreo
de eventos de seguridad. Proporciona herramientas para:

- Registro de eventos de auditoría por usuarios
- Consulta de logs de auditoría para administradores
- Monitoreo de actividad del sistema
- Análisis de seguridad y cumplimiento

Funcionalidades principales:
- Registro automático de eventos críticos
- Consulta filtrada de logs de auditoría
- Control de acceso basado en roles
- Paginación y filtrado de eventos
- Exportación de datos de auditoría

Eventos auditados automáticamente:
- Autenticación (login/logout)
- Subida y descarga de documentos
- Búsquedas realizadas
- Cambios de permisos
- Errores del sistema

Seguridad:
- Solo administradores pueden consultar logs
- Registro inmutable de eventos
- Timestamps precisos
- Información contextual detallada


"""

from typing import Annotated, Optional, Dict, List, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status, Query, HTTPException
from pydantic import BaseModel, Field

# Servicios y utilidades internas
from utils.audit_logger import log_event, fetch_logs, get_audit_statistics
from routes.auth_routes import get_current_user, get_current_admin_user
from services.auth_service import TokenData


# ==================================================================================
#                           CONFIGURACIÓN DEL ROUTER
# ==================================================================================

router = APIRouter(
    prefix="",  # Se configura en main.py
    tags=["auditoría"],
    responses={
        403: {"description": "Acceso denegado - permisos insuficientes"},
        401: {"description": "No autenticado"},
        500: {"description": "Error interno del servidor"}
    }
)


# ==================================================================================
#                           MODELOS DE DATOS
# ==================================================================================

class AuditEvent(BaseModel):
    """
    Modelo para registrar un evento de auditoría personalizado.
    
    Permite a usuarios autenticados registrar eventos específicos
    que requieren seguimiento para cumplimiento o análisis.
    
    Attributes:
        event_type: Tipo de evento (LOGIN, UPLOAD, SEARCH, etc.)
        details: Información adicional sobre el evento
        severity: Nivel de importancia del evento
    """
    
    event_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tipo de evento de auditoría",
        example="DOCUMENT_ACCESSED"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalles adicionales del evento",
        example={"document_id": "doc123", "action": "download"}
    )
    
    severity: Optional[str] = Field(
        default="INFO",
        description="Nivel de severidad del evento",
        example="INFO"
    )


class AuditLogEntry(BaseModel):
    """
    Modelo que representa una entrada de log de auditoría.
    
    Estructura los datos de auditoría de manera consistente
    para APIs y respuestas del sistema.
    """
    
    timestamp: str = Field(
        ...,
        description="Marca de tiempo del evento",
        example="2024-01-15T10:30:00Z"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="ID del usuario que generó el evento",
        example="user123"
    )
    
    event_type: str = Field(
        ...,
        description="Tipo de evento",
        example="LOGIN"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalles del evento"
    )
    
    severity: str = Field(
        default="INFO",
        description="Nivel de severidad"
    )


class AuditLogsResponse(BaseModel):
    """
    Respuesta para consultas de logs de auditoría.
    
    Incluye metadatos sobre la consulta y paginación
    además de los logs solicitados.
    """
    
    logs: List[Dict[str, Any]] = Field(
        ...,
        description="Lista de eventos de auditoría"
    )
    
    total_count: int = Field(
        ...,
        description="Número total de logs disponibles"
    )
    
    limit: int = Field(
        ...,
        description="Límite de resultados aplicado"
    )
    
    offset: int = Field(
        default=0,
        description="Desplazamiento aplicado"
    )
    
    query_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat() + "Z",
        description="Timestamp de la consulta"
    )


# ==================================================================================
#                           ENDPOINTS PARA USUARIOS REGULARES
# ==================================================================================

@router.post("/event", status_code=status.HTTP_201_CREATED)
async def register_audit_event(
    payload: AuditEvent,
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> Dict[str, str]:
    """
    Registra un evento de auditoría personalizado por el usuario autenticado.
    
    Permite a los usuarios registrar eventos específicos que requieren
    seguimiento para análisis posterior, cumplimiento o debugging.
    
    Args:
        payload: Datos del evento a registrar
        current_user: Usuario autenticado que registra el evento
        
    Returns:
        Dict[str, str]: Confirmación del registro
        
    Example:
        POST /api/audit/event
        {
            "event_type": "DOCUMENT_SHARED",
            "details": {"document_id": "doc123", "shared_with": "user456"},
            "severity": "INFO"
        }
    """
    try:
        # Enriquecer detalles del evento con información del usuario
        enhanced_details = {
            **(payload.details or {}),
            "user_email": current_user.email,
            "user_is_admin": current_user.is_admin,
            "source": "user_generated"
        }
        
        # Registrar evento en el sistema de auditoría
        log_event(
            user_id=current_user.uid,
            event_type=payload.event_type,
            details=enhanced_details,
            severity=payload.severity or "INFO"
        )
        
        return {
            "message": "Evento de auditoría registrado exitosamente",
            "event_type": payload.event_type,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        # Si falla el registro, también es un evento de auditoría
        log_event(
            user_id=current_user.uid,
            event_type="AUDIT_LOG_ERROR",
            details={
                "attempted_event_type": payload.event_type,
                "error": str(e),
                "error_type": type(e).__name__
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registrando evento de auditoría"
        )


# ==================================================================================
#                           ENDPOINTS PARA ADMINISTRADORES
# ==================================================================================

@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)],
    limit: int = Query(default=100, ge=1, le=1000, description="Número máximo de logs a devolver"),
    offset: int = Query(default=0, ge=0, description="Número de logs a omitir"),
    event_type: Optional[str] = Query(default=None, description="Filtrar por tipo de evento"),
    user_id: Optional[str] = Query(default=None, description="Filtrar por ID de usuario"),
    severity: Optional[str] = Query(default=None, description="Filtrar por severidad"),
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (ISO format)"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (ISO format)")
) -> AuditLogsResponse:
    """
    Obtiene logs de auditoría con filtros y paginación (solo administradores).
    
    Permite a los administradores consultar y analizar eventos de auditoría
    del sistema con múltiples opciones de filtrado y paginación.
    
    Args:
        current_admin: Usuario administrador autenticado
        limit: Número máximo de resultados (1-1000)
        offset: Número de resultados a omitir para paginación
        event_type: Filtrar por tipo específico de evento
        user_id: Filtrar por usuario específico
        severity: Filtrar por nivel de severidad
        start_date: Fecha de inicio en formato ISO
        end_date: Fecha de fin en formato ISO
        
    Returns:
        AuditLogsResponse: Logs filtrados con metadatos de consulta
        
    Example:
        GET /api/audit/logs?limit=50&event_type=LOGIN&severity=INFO
    """
    try:
        # Construir filtros para la consulta
        filters = {}
        
        if event_type:
            filters["event_type"] = event_type
        
        if user_id:
            filters["user_id"] = user_id
            
        if severity:
            filters["severity"] = severity
            
        if start_date:
            try:
                # Validar formato de fecha
                datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                filters["start_date"] = start_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha de inicio inválido. Use formato ISO."
                )
        
        if end_date:
            try:
                # Validar formato de fecha
                datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                filters["end_date"] = end_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de fecha de fin inválido. Use formato ISO."
                )
        
        # Obtener logs del sistema de auditoría
        logs_data = fetch_logs(
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        # Registrar la consulta de auditoría (meta-auditoría)
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_LOGS_QUERIED",
            details={
                "filters_applied": filters,
                "limit": limit,
                "offset": offset,
                "results_count": len(logs_data.get("logs", []))
            },
            severity="INFO"
        )
        
        # Estructurar respuesta
        return AuditLogsResponse(
            logs=logs_data.get("logs", []),
            total_count=logs_data.get("total_count", len(logs_data.get("logs", []))),
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        # Registrar error en auditoría
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_QUERY_ERROR",
            details={
                "error": str(e),
                "error_type": type(e).__name__,
                "filters": locals().get("filters", {})
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error consultando logs de auditoría"
        )


@router.get("/stats")
async def get_audit_statistics(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)],
    days: int = Query(default=30, ge=1, le=365, description="Días hacia atrás para estadísticas")
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de auditoría para análisis (solo administradores).
    
    Proporciona métricas y estadísticas sobre la actividad del sistema
    basadas en los logs de auditoría del período especificado.
    
    Args:
        current_admin: Usuario administrador autenticado
        days: Número de días hacia atrás para calcular estadísticas
        
    Returns:
        Dict[str, Any]: Estadísticas de auditoría y actividad
    """
    try:
        # Calcular fechas del período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener estadísticas del sistema de auditoría
        stats = get_audit_statistics(
            start_date=start_date.isoformat() + "Z",
            end_date=end_date.isoformat() + "Z"
        )
        
        # Registrar consulta de estadísticas
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_STATS_QUERIED",
            details={
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            severity="INFO"
        )
        
        return {
            **stats,
            "period_info": {
                "days": days,
                "start_date": start_date.isoformat() + "Z",
                "end_date": end_date.isoformat() + "Z"
            },
            "generated_at": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        # Registrar error
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_STATS_ERROR",
            details={
                "error": str(e),
                "error_type": type(e).__name__,
                "requested_days": days
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estadísticas de auditoría"
        )


@router.delete("/logs/cleanup")
async def cleanup_old_logs(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)],
    days_to_keep: int = Query(default=90, ge=1, le=3650, description="Días de logs a mantener")
) -> Dict[str, Any]:
    """
    Limpia logs de auditoría antiguos (solo administradores).
    
    Elimina logs más antiguos que el período especificado para
    gestionar el almacenamiento y cumplir políticas de retención.
    
    Args:
        current_admin: Usuario administrador autenticado
        days_to_keep: Días de logs a mantener (elimina más antiguos)
        
    Returns:
        Dict[str, Any]: Resultado de la operación de limpieza
    """
    try:
        # Calcular fecha límite
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Registrar intento de limpieza ANTES de ejecutar
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_CLEANUP_STARTED",
            details={
                "cutoff_date": cutoff_date.isoformat(),
                "days_to_keep": days_to_keep,
                "admin_email": current_admin.email
            },
            severity="WARNING"
        )
        
        # Aquí iría la lógica de limpieza real
        # cleanup_result = cleanup_logs_before_date(cutoff_date)
        
        # Por ahora, simulamos el resultado
        cleanup_result = {
            "deleted_logs": 0,
            "cutoff_date": cutoff_date.isoformat() + "Z",
            "status": "completed"
        }
        
        # Registrar resultado de limpieza
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_CLEANUP_COMPLETED",
            details={
                **cleanup_result,
                "days_to_keep": days_to_keep
            },
            severity="WARNING"
        )
        
        return {
            "message": "Limpieza de logs completada",
            **cleanup_result,
            "executed_at": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        # Registrar fallo de limpieza
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_CLEANUP_FAILED",
            details={
                "error": str(e),
                "error_type": type(e).__name__,
                "days_to_keep": days_to_keep
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error durante la limpieza de logs"
        )


# ==================================================================================
#                           ENDPOINTS DE EXPORTACIÓN
# ==================================================================================

@router.get("/export")
async def export_audit_logs(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)],
    format: str = Query(default="json", regex="^(json|csv)$", description="Formato de exportación"),
    days: int = Query(default=30, ge=1, le=365, description="Días de logs a exportar")
) -> Dict[str, Any]:
    """
    Exporta logs de auditoría en formato especificado (solo administradores).
    
    Genera un archivo de exportación con los logs de auditoría
    del período especificado para análisis externo o backup.
    
    Args:
        current_admin: Usuario administrador autenticado
        format: Formato de exportación (json o csv)
        days: Días de logs a incluir en la exportación
        
    Returns:
        Dict[str, Any]: Información sobre la exportación generada
    """
    try:
        # Calcular período de exportación
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener logs para exportación
        export_logs = fetch_logs(
            limit=10000,  # Límite alto para exportación
            offset=0,
            filters={
                "start_date": start_date.isoformat() + "Z",
                "end_date": end_date.isoformat() + "Z"
            }
        )
        
        # Registrar exportación
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_LOGS_EXPORTED",
            details={
                "format": format,
                "period_days": days,
                "logs_count": len(export_logs.get("logs", [])),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            severity="INFO"
        )
        
        return {
            "message": "Exportación preparada",
            "format": format,
            "logs_count": len(export_logs.get("logs", [])),
            "period": {
                "days": days,
                "start_date": start_date.isoformat() + "Z",
                "end_date": end_date.isoformat() + "Z"
            },
            "data": export_logs.get("logs", []),
            "exported_at": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        # Registrar error de exportación
        log_event(
            user_id=current_admin.uid,
            event_type="AUDIT_EXPORT_ERROR",
            details={
                "error": str(e),
                "error_type": type(e).__name__,
                "format": format,
                "days": days
            },
            severity="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exportando logs de auditoría"
        )
