from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
# from models.document_model import DocumentCreate, DocumentResponse # Importaremos después
# from services.gemini_service import ...
# from services.meilisearch_service import ...
# from services.firebase_service import ...
# from utils.audit_logger import log_event

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Lógica para subir, procesar con Gemini, indexar (implementaremos después)
    return {"message": f"Subida de '{file.filename}' en desarrollo."}

@router.get("/search")
async def search_documents(query: str):
    # Lógica para buscar con Meilisearch (implementaremos después)
    return {"message": f"Búsqueda para '{query}' en desarrollo."}

@router.get("/download/{document_id}")
async def download_document(document_id: str):
    # Lógica para descargar desde Firebase Storage (implementaremos después)
    return {"message": f"Descarga de '{document_id}' en desarrollo."}

@router.get("/list")
async def list_documents():
    # Lógica para listar documentos (implementaremos después)
    return {"message": "Listado de documentos en desarrollo."}