# backend/utils/audit_logger.py
from typing import List, Dict, Any, Optional
from firebase_admin import firestore
from services.firebase_service import get_firestore_client
from datetime import datetime

# ---------- Registrar evento ----------
def log_event(user_id: Optional[str], event_type: str, details: Optional[dict] = None) -> None:
    """
    Guarda un evento de auditoría en la colección 'audit_logs'.
    """
    details = details or {}

    firestore_client = get_firestore_client()
    firestore_client.collection("audit_logs").add({
        "timestamp": firestore.SERVER_TIMESTAMP,   # Hora generada por Firestore
        "user_id": user_id,
        "event_type": event_type,
        "details": details,
    })

# ---------- Obtener logs ----------
def fetch_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Devuelve los últimos `limit` eventos ordenados por fecha descendente.
    """
    firestore_client = get_firestore_client()
    query = (
        firestore_client.collection("audit_logs")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [
        {**doc.to_dict(), "id": doc.id}
        for doc in query.stream()
    ]

def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Alias for fetch_logs - returns recent audit logs.
    """
    return fetch_logs(limit)
