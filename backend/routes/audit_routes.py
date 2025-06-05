# backend/routes/audit_routes.py
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from utils.audit_logger import log_event, fetch_logs
from routes.auth_routes import get_current_user, get_current_admin_user
from services.auth_service import TokenData

router = APIRouter()

# ---------- Modelos ----------
class AuditEvent(BaseModel):
    event_type: str           # p. ej. LOGIN, LOGOUT, UPLOAD
    details: Optional[dict] = None

# ---------- Endpoints ----------
@router.post("/event", status_code=status.HTTP_201_CREATED)
async def add_audit_event(
    payload: AuditEvent,
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Guarda un evento de auditoría del usuario autenticado.
    """
    log_event(current_user.uid, payload.event_type, payload.details)
    return {"message": "Event logged."}

@router.get("/logs")
async def list_audit_logs(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)],  # ← primero el obligatorio
    limit: int = 100                                                       # ← luego el opcional
):
    """
    Devuelve los últimos `limit` eventos de auditoría. Solo para admins.
    """
    return {"logs": fetch_logs(limit)}
