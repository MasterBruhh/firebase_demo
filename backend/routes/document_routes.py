# backend/routes/document_routes.py
import os, json, uuid, mimetypes
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from services.firebase_service import upload_file_to_storage, download_file_from_storage, list_files_in_storage
from services.meilisearch_service import add_documents, search_documents
from services.gemini_service import extract_metadata
from models.document_model import DocumentMetadata
from pathlib import Path

router = APIRouter()

ROOT = Path(__file__).resolve().parents[1]  # …/backend
LOCAL_META_DIR = ROOT / ".." / "meilisearch-data" / "indexes" / "documents"
LOCAL_META_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File is empty")

    # 1) Sube a Firebase Storage con la ruta fecha-based
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
    storage_path = upload_file_to_storage(file_bytes, file.filename, content_type)

    # 2) Metadata estilo Gemini extractor
    meta = extract_metadata(file_bytes, file.filename)
    meta.update(
        {
            "storage_path": storage_path,
            "media_type": content_type or "application/octet-stream",
        }
    )

    # 3) Guarda JSON local con nombre del archivo
    json_name = f"{Path(file.filename).stem}.json"
    json_path = LOCAL_META_DIR / json_name
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Metadata guardada en {json_path.relative_to(ROOT.parent)}")

    # 4) Indexa en MeiliSearch
    add_documents([meta])

    return meta

# ---------------------------------------------------------------------------
@router.get("/search")
async def search_docs(query: str):
    """
    Devuelve hits de MeiliSearch.
    """
    return search_documents(query)

# ---------------------------------------------------------------------------
@router.get("/download/{file_stem}")
async def download(file_stem: str):
    json_path = LOCAL_META_DIR / f"{file_stem}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    meta = json.loads(json_path.read_text(encoding="utf-8"))
    blob_bytes = download_file_from_storage(meta["storage_path"])

    return StreamingResponse(
        iter([blob_bytes]),
        media_type=meta["media_type"],
        headers={"Content-Disposition": f'attachment; filename="{meta["filename"]}"'},
    )

# ---------------------------------------------------------------------------
@router.get("/list")
async def list_all():
    docs = [
        json.loads((LOCAL_META_DIR / f).read_text(encoding="utf-8"))
        for f in os.listdir(LOCAL_META_DIR)
        if f.endswith(".json")
    ]
    return {"documents": docs}

# ---------- NUEVO: listar todo lo que hay en Firebase Storage ----------
@router.get("/storage")
async def list_storage(prefix: str = "documents/"):
    """
    Devuelve todos los blobs que existen en Firebase Storage bajo 'documents/'.
    """
    return {"files": list_files_in_storage(prefix)}

# ---------- NUEVO: descargar por ruta completa ----------
@router.get("/download_by_path")
async def download_by_path(path: str = Query(..., description="Blob path in Storage")):
    """
    Descarga cualquier blob dado su `path` completo (documents/…/file.ext).
    """
    try:
        blob_bytes = download_file_from_storage(path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    filename = Path(path).name
    media = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return StreamingResponse(
        iter([blob_bytes]),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
