# backend/utils/audit_logger.py

from services.firebase_service import get_firestore_client
from datetime import datetime
from firebase_admin import firestore

def log_event(user_id: str | None, event_type: str, details: dict = None):
    """
    Registra un evento de auditoría en Firestore de forma síncrona.
    :param user_id: ID del usuario que realizó la acción (puede ser None).
    :param event_type: Tipo de evento ('LOGIN', 'UPLOAD', etc.).
    :param details: Diccionario con detalles adicionales del evento.
    """
    if details is None:
        details = {}

    try:
        firestore_client = get_firestore_client()
        audit_log_ref = firestore_client.collection("audit_logs")

        log_entry = {
            "timestamp": datetime.now(),  # Hora local del backend
            "user_id": user_id,
            "event_type": event_type,
            "details": details
        }

        audit_log_ref.add(log_entry)

        # print(f"Evento de auditoría registrado: {event_type} por {user_id or 'Sistema'}")

    except Exception as e:
        print(f"ADVERTENCIA: No se pudo registrar el evento de auditoría en Firestore: {e}")
