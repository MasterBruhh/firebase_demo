# backend/services/meilisearch_service.py
from typing import List, Dict
from meilisearch import Client
from config import settings

client: Client | None = None
INDEX_NAME = "documents"

# ---------------------------------------------------------------------------
def initialize_meilisearch() -> None:
    """
    Inicializa el cliente global y crea el índice 'documents' si no existe.
    Lanza RuntimeError con un mensaje claro cuando:
        • la URL es incorrecta / servicio caído
        • la API-key no coincide
    """
    global client
    if client:
        return  # ya inicializado

    client = Client(
        settings.MEILISEARCH_HOST,
        settings.MEILISEARCH_MASTER_KEY or None
    )

    # --- prueba de conexión / clave ---
    try:
        raw = client.get_indexes()            # ↩︎ puede ser list o dict
    except Exception as exc:
        raise RuntimeError(f"No se pudo conectar a MeiliSearch: {exc}") from exc

    # raw → lista de índices
    if isinstance(raw, dict):
        # ¿vino envuelto en {"results": [...]} ?
        if "results" in raw:
            raw = raw["results"]
        # ¿vino un error {message, code,…}?
        elif "message" in raw:
            raise RuntimeError(
                f"MeiliSearch error: {raw['message']} (code={raw.get('code')})"
            )
        else:
            raise RuntimeError(f"Respuesta inesperada de MeiliSearch: {raw}")

# --- crea índice si no existe ---
    if isinstance(raw, list):
        index_uids = [
            idx["uid"] if isinstance(idx, dict) else idx.uid      # ← aquí
            for idx in raw
        ]
    else:
        raise RuntimeError(f"Respuesta inesperada de MeiliSearch: {raw}")

    if INDEX_NAME not in index_uids:
        # Para SDK < 2.0
        client.create_index(INDEX_NAME, {"primaryKey": "id"})



    print("MeiliSearch inicializado.")

# ---------------------------------------------------------------------------
def get_client() -> Client:
    if client is None:
        raise RuntimeError("Debe llamarse initialize_meilisearch() primero")
    return client

# ---------------------------------------------------------------------------
def add_documents(documents: List[Dict]) -> None:
    initialize_meilisearch()
    get_client().index(INDEX_NAME).add_documents(documents)
    print(f"{len(documents)} documento(s) añadidos a MeiliSearch.")

def search_documents(query: str, limit: int = 20):
    initialize_meilisearch()
    return get_client().index(INDEX_NAME).search(query, {"limit": limit})
