"""
Rutas de Gestión de Documentos - API REST para Documentos

Este módulo define todas las rutas y endpoints relacionados con la gestión
de documentos en el sistema. Proporciona una API REST completa para:

- Subida de documentos con análisis automático de metadatos
- Búsqueda semántica y filtrada de documentos
- Descarga segura de archivos almacenados
- Listado y navegación de documentos disponibles
- Integración con Firebase Storage y Meilisearch

Endpoints disponibles:
- POST /upload: Sube un documento y extrae metadatos automáticamente
- GET /search: Búsqueda inteligente de documentos por contenido
- GET /download/{file_stem}: Descarga directa por ID de documento
- GET /download_by_path: Descarga por ruta completa en storage
- GET /list: Lista todos los documentos disponibles
- GET /storage: Explora archivos en Firebase Storage

Flujo de procesamiento de documentos:
1. Recepción del archivo por HTTP multipart
2. Subida a Firebase Storage con organización por fechas
3. Extracción de metadatos con Gemini AI
4. Persistencia local de metadatos en JSON
5. Indexado en Meilisearch para búsquedas
6. Respuesta con metadatos completos al cliente

Características de seguridad:
- Validación de tipos de archivo
- Sanitización de nombres de archivo
- Control de tamaño máximo de uploads
- Paths seguros para almacenamiento


"""

import os
import json
import uuid
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Depends
from fastapi.responses import StreamingResponse

# Servicios internos
from services.firebase_service import upload_file_to_storage, download_file_from_storage, list_files_in_storage
from services.meilisearch_service import add_documents, search_documents
from services.gemini_service import extract_metadata, is_supported_file, estimate_processing_time

# Modelos y utilidades
from models.document_model import DocumentMetadata
from utils.audit_logger import log_event


# ==================================================================================
#                           CONFIGURACIÓN DEL ROUTER
# ==================================================================================

# Router principal para todas las rutas de documentos
router = APIRouter(
    prefix="",  # Se configura en main.py
    tags=["documentos"],
    responses={
        404: {"description": "Documento no encontrado"},
        400: {"description": "Error en los datos de entrada"},
        500: {"description": "Error interno del servidor"}
    }
)

# ==================================================================================
#                           CONFIGURACIÓN DE DIRECTORIOS
# ==================================================================================

# Directorio raíz del backend
ROOT_DIR = Path(__file__).resolve().parents[1]  # .../backend

# Directorio para almacenar metadatos localmente (backup y cache)
LOCAL_METADATA_DIR = ROOT_DIR / ".." / "meilisearch-data" / "indexes" / "documents"
LOCAL_METADATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuraciones de archivos
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB máximo
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.md'}


# ==================================================================================
#                           FUNCIONES AUXILIARES
# ==================================================================================

def _validate_uploaded_file(file: UploadFile) -> None:
    """
    Valida un archivo subido antes del procesamiento.
    
    Verifica el tamaño, tipo y seguridad del archivo para
    prevenir uploads maliciosos o problemáticos.
    
    Args:
        file: Archivo subido por el usuario
        
    Raises:
        HTTPException: Si el archivo no pasa las validaciones
    """
    # Validar que el archivo tenga nombre
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener un nombre válido"
        )
    
    # Validar extensión del archivo
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado. Tipos permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validar que el nombre no contenga caracteres peligrosos
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in file.filename for char in dangerous_chars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del archivo contiene caracteres no permitidos"
        )


def _save_metadata_locally(metadata: Dict[str, Any], filename: str) -> Path:
    """
    Guarda los metadatos del documento en el sistema de archivos local.
    
    Esto sirve como backup y para consultas rápidas sin depender
    de servicios externos.
    
    Args:
        metadata: Metadatos extraídos del documento
        filename: Nombre original del archivo
        
    Returns:
        Path: Ruta donde se guardaron los metadatos
    """
    # Crear nombre del archivo JSON basado en el archivo original
    json_filename = f"{Path(filename).stem}.json"
    json_path = LOCAL_METADATA_DIR / json_filename
    
    # Guardar metadatos con formato legible
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)
    
    # Mensaje de depuración - comentado para producción
    # print(f"📁 Metadatos guardados en: {json_path.relative_to(ROOT_DIR.parent)}")
    
    return json_path


def _generate_unique_filename(original_filename: str) -> str:
    """
    Genera un nombre único para evitar colisiones en el storage.
    
    Args:
        original_filename: Nombre original del archivo
        
    Returns:
        str: Nombre único manteniendo la extensión original
    """
    path = Path(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{path.stem}_{timestamp}_{unique_id}{path.suffix}"


# ==================================================================================
#                           ENDPOINTS DE SUBIDA DE DOCUMENTOS
# ==================================================================================

@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)) -> DocumentMetadata:
    """
    Sube un documento y extrae automáticamente sus metadatos.
    
    Este endpoint orquesta todo el proceso de subida y análisis:
    1. Valida el archivo subido
    2. Lee el contenido del archivo
    3. Sube el archivo a Firebase Storage
    4. Extrae metadatos usando Gemini AI
    5. Guarda metadatos localmente (backup)
    6. Indexa el documento en Meilisearch
    7. Registra la operación en logs de auditoría
    
    Args:
        file: Archivo a subir (PDF, DOCX, PPTX, XLSX, TXT, MD)
        
    Returns:
        DocumentMetadata: Metadatos completos del documento procesado
        
    Raises:
        HTTPException 400: Si el archivo es inválido o está vacío
        HTTPException 413: Si el archivo excede el tamaño máximo
        HTTPException 500: Si hay errores durante el procesamiento
        
    Example:
        # Desde el frontend con FormData
        formData = new FormData();
        formData.append('file', selectedFile);
        
        fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        })
    """
    try:
        # ===== VALIDACIÓN INICIAL DEL ARCHIVO =====
        _validate_uploaded_file(file)
        
        # Estimar tiempo de procesamiento para el usuario
        estimated_time = "desconocido"
        if hasattr(file, 'size') and file.size:
            estimated_time = f"{estimate_processing_time(file.size)} segundos"
        
        # Mensaje de depuración - comentado para producción
        # print(f"📤 Iniciando subida: {file.filename} (tiempo estimado: {estimated_time})")
        
        # ===== LECTURA DEL CONTENIDO DEL ARCHIVO =====
        file_bytes = await file.read()
        
        # Validar que el archivo no esté vacío
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío"
            )
        
        # Validar tamaño máximo
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE // (1024*1024)}MB)"
            )
        
        # ===== SUBIDA A FIREBASE STORAGE =====
        # Detectar tipo MIME del archivo
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        # Generar nombre único para evitar colisiones
        unique_filename = _generate_unique_filename(file.filename)
        
        # Subir archivo a Firebase Storage con organización por fechas
        storage_path = upload_file_to_storage(file_bytes, unique_filename, content_type)
        
        # ===== EXTRACCIÓN DE METADATOS CON GEMINI AI =====
        # Extraer metadatos usando IA
        extracted_metadata = extract_metadata(file_bytes, file.filename)
        
        # Enriquecer metadatos con información adicional
        complete_metadata = {
            **extracted_metadata,  # Metadatos de Gemini
            "storage_path": storage_path,
            "media_type": content_type,
            "original_filename": file.filename,
            "unique_filename": unique_filename,
            "upload_timestamp": datetime.now().isoformat() + "Z",
            "file_hash": str(hash(file_bytes)),  # Hash simple para verificación
            "processing_time_estimate": estimated_time
        }
        
        # ===== PERSISTENCIA LOCAL DE METADATOS =====
        # Guardar metadatos localmente como backup
        metadata_path = _save_metadata_locally(complete_metadata, file.filename)
        
        # ===== INDEXADO EN MEILISEARCH =====
        # Indexar documento para búsquedas
        try:
            add_documents([complete_metadata])
            # print(f"🔍 Documento indexado en Meilisearch: {file.filename}")
        except Exception as e:
            # No fallar si Meilisearch no está disponible, pero registrar el error
            # print(f"⚠️  Error indexando en Meilisearch: {e}")
            pass
        
        # ===== REGISTRO DE AUDITORÍA =====
        log_event('system', 'DOCUMENT_UPLOADED', {
            'filename': file.filename,
            'storage_path': storage_path,
            'file_size': len(file_bytes),
            'content_type': content_type,
            'processing_status': 'success'
        })
        
        # ===== RESPUESTA EXITOSA =====
        # print(f"✅ Documento procesado exitosamente: {complete_metadata['title']}")
        
        # Convertir a modelo Pydantic para validación y respuesta
        return DocumentMetadata(**complete_metadata)
        
    except HTTPException:
        # Re-lanzar HTTPExceptions tal como están
        raise
    except Exception as e:
        # Manejar errores inesperados
        error_detail = f"Error procesando documento: {str(e)}"
        
        # Registrar error en auditoría
        log_event('system', 'DOCUMENT_UPLOAD_ERROR', {
            'filename': file.filename if file and file.filename else 'unknown',
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


# ==================================================================================
#                           ENDPOINTS DE BÚSQUEDA DE DOCUMENTOS
# ==================================================================================

@router.get("/search")
async def search_documents_endpoint(
    query: str = Query(..., description="Términos de búsqueda", min_length=1),
    limit: int = Query(default=20, ge=1, le=100, description="Número máximo de resultados"),
    offset: int = Query(default=0, ge=0, description="Número de resultados a omitir")
) -> Dict[str, Any]:
    """
    Busca documentos por contenido usando búsqueda semántica.
    
    Utiliza Meilisearch para realizar búsquedas inteligentes que incluyen:
    - Búsqueda por título, resumen y contenido
    - Búsqueda por palabras clave
    - Tolerancia a errores tipográficos
    - Ranking por relevancia
    - Filtros y facetas
    
    Args:
        query: Términos de búsqueda (requerido)
        limit: Máximo número de resultados a devolver (1-100)
        offset: Número de resultados a omitir para paginación
        
    Returns:
        Dict[str, Any]: Resultados de búsqueda con metadatos y estadísticas
        
    Example:
        GET /api/documents/search?query=contrato&limit=10&offset=0
    """
    try:
        # Validar parámetros de entrada
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La consulta de búsqueda no puede estar vacía"
            )
        
        # Realizar búsqueda en Meilisearch
        search_results = search_documents(
            query=query.strip(),
            limit=limit,
            offset=offset
        )
        
        # Registrar búsqueda en auditoría
        log_event('system', 'DOCUMENT_SEARCH', {
            'query': query,
            'results_count': len(search_results.get('hits', [])),
            'limit': limit,
            'offset': offset
        })
        
        return search_results
        
    except Exception as e:
        # Manejar errores de búsqueda
        log_event('system', 'SEARCH_ERROR', {
            'query': query,
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error realizando búsqueda: {str(e)}"
        )


# ==================================================================================
#                           ENDPOINTS DE DESCARGA DE DOCUMENTOS
# ==================================================================================

@router.get("/download/{file_stem}")
async def download_document(file_stem: str) -> StreamingResponse:
    """
    Descarga un documento por su ID (nombre sin extensión).
    
    Busca los metadatos del documento localmente y descarga
    el archivo desde Firebase Storage.
    
    Args:
        file_stem: ID del documento (nombre sin extensión)
        
    Returns:
        StreamingResponse: Archivo para descarga con headers apropiados
        
    Raises:
        HTTPException 404: Si el documento no existe
        HTTPException 500: Si hay errores durante la descarga
    """
    try:
        # Buscar metadatos del documento
        metadata_path = LOCAL_METADATA_DIR / f"{file_stem}.json"
        
        if not metadata_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento '{file_stem}' no encontrado"
            )
        
        # Cargar metadatos del documento
        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)
        
        # Descargar archivo desde Firebase Storage
        file_bytes = download_file_from_storage(metadata["storage_path"])
        
        # Preparar headers para descarga
        filename = metadata.get("original_filename", metadata.get("filename", f"{file_stem}.bin"))
        content_type = metadata.get("media_type", "application/octet-stream")
        
        # Registrar descarga en auditoría
        log_event('system', 'DOCUMENT_DOWNLOADED', {
            'file_stem': file_stem,
            'filename': filename,
            'storage_path': metadata["storage_path"]
        })
        
        # Devolver archivo como stream
        return StreamingResponse(
            iter([file_bytes]),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        # Manejar errores de descarga
        log_event('system', 'DOWNLOAD_ERROR', {
            'file_stem': file_stem,
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando documento: {str(e)}"
        )


@router.get("/download_by_path")
async def download_by_storage_path(
    path: str = Query(..., description="Ruta completa del archivo en Firebase Storage")
) -> StreamingResponse:
    """
    Descarga un documento directamente por su ruta en Firebase Storage.
    
    Este endpoint permite descargar archivos cuando se conoce
    la ruta exacta en el storage, útil para integraciones externas.
    
    Args:
        path: Ruta completa del archivo en Storage (ej: "documents/2024/01/file.pdf")
        
    Returns:
        StreamingResponse: Archivo para descarga
        
    Raises:
        HTTPException 404: Si el archivo no existe en Storage
        HTTPException 400: Si la ruta es inválida
    """
    try:
        # Validar que la ruta no esté vacía
        if not path.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ruta del archivo no puede estar vacía"
            )
        
        # Sanitizar ruta para prevenir path traversal
        if ".." in path or path.startswith("/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ruta de archivo no válida"
            )
        
        # Descargar archivo desde Firebase Storage
        file_bytes = download_file_from_storage(path)
        
        # Extraer nombre del archivo y detectar tipo MIME
        filename = Path(path).name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        
        # Registrar descarga en auditoría
        log_event('system', 'DOCUMENT_DOWNLOADED_BY_PATH', {
            'storage_path': path,
            'filename': filename
        })
        
        # Devolver archivo como stream
        return StreamingResponse(
            iter([file_bytes]),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        # Manejar errores de descarga
        log_event('system', 'DOWNLOAD_BY_PATH_ERROR', {
            'storage_path': path,
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando archivo: {str(e)}"
        )


# ==================================================================================
#                           ENDPOINTS DE LISTADO Y NAVEGACIÓN
# ==================================================================================

@router.get("/list")
async def list_all_documents() -> Dict[str, List[Dict[str, Any]]]:
    """
    Lista todos los documentos disponibles con sus metadatos.
    
    Carga todos los documentos desde el almacenamiento local
    de metadatos y devuelve una lista completa.
    
    Returns:
        Dict[str, List[Dict]]: Lista de documentos con metadatos
    """
    try:
        documents = []
        
        # Iterar sobre todos los archivos JSON de metadatos
        if LOCAL_METADATA_DIR.exists():
            for json_file in LOCAL_METADATA_DIR.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        metadata = json.load(file)
                        documents.append(metadata)
                except Exception as e:
                    # Omitir archivos JSON corruptos
                    # print(f"⚠️  Error leyendo {json_file}: {e}")
                    continue
        
        # Ordenar documentos por fecha de subida (más recientes primero)
        documents.sort(
            key=lambda doc: doc.get("upload_timestamp", doc.get("processing_timestamp", "")),
            reverse=True
        )
        
        # Registrar listado en auditoría
        log_event('system', 'DOCUMENTS_LISTED', {
            'total_documents': len(documents)
        })
        
        return {"documents": documents}
        
    except Exception as e:
        # Manejar errores de listado
        log_event('system', 'LIST_DOCUMENTS_ERROR', {
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando documentos: {str(e)}"
        )


@router.get("/storage")
async def list_storage_files(
    prefix: str = Query(default="documents/", description="Prefijo para filtrar archivos")
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Lista todos los archivos disponibles en Firebase Storage.
    
    Explora Firebase Storage y devuelve una lista de todos
    los archivos disponibles bajo el prefijo especificado.
    
    Args:
        prefix: Prefijo de ruta para filtrar archivos (default: "documents/")
        
    Returns:
        Dict[str, List[str]]: Lista de rutas de archivos en Storage
    """
    try:
        # Listar archivos en Firebase Storage
        storage_files = list_files_in_storage(prefix)
        
        # Registrar exploración en auditoría
        log_event('system', 'STORAGE_EXPLORED', {
            'prefix': prefix,
            'files_count': len(storage_files)
        })
        
        return {"files": storage_files}
        
    except Exception as e:
        # Manejar errores de exploración
        log_event('system', 'STORAGE_EXPLORATION_ERROR', {
            'prefix': prefix,
            'error': str(e),
            'error_type': type(e).__name__
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error explorando storage: {str(e)}"
        )


# ==================================================================================
#                           ENDPOINTS ADICIONALES DE UTILIDAD
# ==================================================================================

@router.get("/stats")
async def get_documents_statistics() -> Dict[str, Any]:
    """
    Obtiene estadísticas de los documentos almacenados.
    
    Returns:
        Dict[str, Any]: Estadísticas del sistema de documentos
    """
    try:
        total_documents = 0
        total_size = 0
        file_types = {}
        
        # Analizar documentos locales
        if LOCAL_METADATA_DIR.exists():
            for json_file in LOCAL_METADATA_DIR.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        metadata = json.load(file)
                        total_documents += 1
                        total_size += metadata.get("file_size_bytes", 0)
                        
                        file_ext = metadata.get("file_extension", "unknown")
                        file_types[file_ext] = file_types.get(file_ext, 0) + 1
                        
                except:
                    continue
        
        stats = {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "average_size_mb": round((total_size / total_documents) / (1024 * 1024), 2) if total_documents > 0 else 0,
            "storage_directory": str(LOCAL_METADATA_DIR),
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )
