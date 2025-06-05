# backend/models/document_model.py
from typing import List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """
    Modelo de respuesta para /documents/upload
    — Compatible con el dict que produce document_routes.py
    — Permite poblar usando 'filename' (nombre actual) o 'file_name' (alias)
    """

    id: str
    filename: str = Field(..., alias="file_name")
    file_extension: str
    file_size_bytes: int
    title: str
    summary: str
    keywords: List[str]
    date: str
    storage_path: str
    media_type: str

    # --- Configuración Pydantic v2 ---
    model_config = {
        # Acepta tanto filename como file_name al crear la instancia
        "populate_by_name": True,
        # Cuando FastAPI serializa la respuesta usará los nombres de campo
        # (filename) y no los alias, a menos que se le indique by_alias=True.
        # De este modo tu salida seguirá viéndose como ahora.
    }
