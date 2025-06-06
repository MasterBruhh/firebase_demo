"""
Modelos de Datos - Estructuras de Documentos

Este módulo define los modelos de datos utilizando Pydantic para la validación
automática y serialización de datos relacionados con documentos. Los modelos
aseguran la consistencia de datos entre el frontend y backend.

Modelos incluidos:
- DocumentMetadata: Metadatos completos de un documento procesado
- DocumentSearchResult: Resultado de búsqueda con información destacada
- DocumentUploadResponse: Respuesta del proceso de subida

Características de Pydantic:
- Validación automática de tipos de datos
- Serialización/deserialización JSON
- Generación automática de esquemas OpenAPI
- Manejo de alias para compatibilidad
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================================================================================
#                           MODELO PRINCIPAL DE DOCUMENTO
# ==================================================================================

class DocumentMetadata(BaseModel):
    """
    Modelo de metadatos completos de un documento procesado.
    
    Este modelo representa toda la información extraída y generada para un documento:
    - Identificación única y información del archivo
    - Metadatos extraídos por IA (Gemini)
    - Ubicación en el almacenamiento
    - Fechas de procesamiento
    
    El modelo utiliza Pydantic v2 para validación automática y está optimizado
    para ser utilizado tanto en respuestas de API como en indexación de búsqueda.
    
    Attributes:
        id: Identificador único del documento (generado automáticamente)
        filename: Nombre original del archivo
        file_extension: Extensión del archivo (.pdf, .docx, etc.)
        file_size_bytes: Tamaño del archivo en bytes
        title: Título extraído por IA o derivado del nombre de archivo
        summary: Resumen del contenido generado por IA
        keywords: Lista de palabras clave extraídas por IA
        date: Fecha del documento (extraída por IA o fecha de procesamiento)
        storage_path: Ruta del archivo en Cloud Storage
        media_type: Tipo MIME del archivo
    """
    
    # ===== IDENTIFICACIÓN DEL DOCUMENTO =====
    id: str = Field(
        ...,
        description="Identificador único del documento (UUID)",
        example="doc_123e4567-e89b-12d3-a456-426614174000"
    )
    
    # ===== INFORMACIÓN DEL ARCHIVO =====
    filename: str = Field(
        ..., 
        alias="file_name",  # Permite usar tanto 'filename' como 'file_name'
        description="Nombre original del archivo subido",
        example="contrato_empresa_2024.pdf"
    )
    
    file_extension: str = Field(
        ...,
        description="Extensión del archivo (incluye el punto)",
        example=".pdf"
    )
    
    file_size_bytes: int = Field(
        ...,
        description="Tamaño del archivo en bytes",
        ge=0,  # Mayor o igual a 0
        example=1048576  # 1 MB
    )
    
    media_type: str = Field(
        ...,
        description="Tipo MIME del archivo",
        example="application/pdf"
    )
    
    # ===== METADATOS EXTRAÍDOS POR IA =====
    title: str = Field(
        ...,
        description="Título del documento extraído por IA",
        example="Contrato de Servicios Profesionales 2024"
    )
    
    summary: str = Field(
        ...,
        description="Resumen del contenido generado por Google Gemini",
        example="Contrato que establece los términos y condiciones para la prestación de servicios profesionales..."
    )
    
    keywords: List[str] = Field(
        ...,
        description="Lista de palabras clave extraídas por IA",
        example=["contrato", "servicios", "legal", "términos", "condiciones"]
    )
    
    date: str = Field(
        ...,
        description="Fecha del documento en formato YYYY-MM-DD (extraída por IA)",
        example="2024-06-05"
    )
    
    # ===== INFORMACIÓN DE ALMACENAMIENTO =====
    storage_path: str = Field(
        ...,
        description="Ruta del archivo en Cloud Storage",
        example="documents/2024/06/05/contrato_empresa_2024.pdf"
    )

    # ===== CONFIGURACIÓN DE PYDANTIC V2 =====
    model_config = {
        # Permite usar tanto 'filename' como 'file_name' al crear instancias
        # Esto asegura compatibilidad con el código existente que puede usar cualquiera de los dos nombres
        "populate_by_name": True,
        
        # Ejemplo para la documentación automática de OpenAPI/Swagger
        "json_schema_extra": {
            "example": {
                "id": "doc_123e4567-e89b-12d3-a456-426614174000",
                "filename": "informe_anual_2024.pdf",
                "file_extension": ".pdf",
                "file_size_bytes": 2048000,
                "title": "Informe Anual de Actividades 2024",
                "summary": "Documento que presenta los logros y resultados obtenidos durante el año 2024, incluyendo métricas de desempeño, objetivos cumplidos y planes futuros.",
                "keywords": ["informe", "anual", "resultados", "actividades", "2024"],
                "date": "2024-12-31",
                "storage_path": "documents/2024/06/05/informe_anual_2024.pdf",
                "media_type": "application/pdf"
            }
        }
    }


# ==================================================================================
#                           MODELOS DE RESPUESTA DE BÚSQUEDA
# ==================================================================================

class DocumentSearchResult(BaseModel):
    """
    Modelo para resultados de búsqueda con información destacada.
    
    Extiende DocumentMetadata con información específica de búsqueda como
    puntuación de relevancia y texto destacado.
    
    Attributes:
        document: Metadatos completos del documento
        score: Puntuación de relevancia (0.0 a 1.0)
        highlighted: Texto con términos de búsqueda destacados
    """
    
    document: DocumentMetadata = Field(
        ...,
        description="Metadatos completos del documento encontrado"
    )
    
    score: Optional[float] = Field(
        default=None,
        description="Puntuación de relevancia del resultado (0.0 a 1.0)",
        ge=0.0,
        le=1.0,
        example=0.85
    )
    
    highlighted: Optional[Dict[str, str]] = Field(
        default=None,
        description="Campos con términos de búsqueda destacados usando <mark>",
        example={
            "title": "Contrato de <mark>Servicios</mark> Profesionales",
            "summary": "Documento que establece <mark>términos</mark> y condiciones..."
        }
    )


# ==================================================================================
#                           MODELOS DE RESPUESTA DE SUBIDA
# ==================================================================================

class DocumentUploadResponse(BaseModel):
    """
    Modelo de respuesta para el endpoint de subida de documentos.
    
    Proporciona información sobre el resultado del procesamiento:
    - Metadatos extraídos
    - Estado del procesamiento
    - Información de indexación
    
    Attributes:
        success: Indica si el procesamiento fue exitoso
        message: Mensaje descriptivo del resultado
        document: Metadatos del documento procesado
        processing_time_ms: Tiempo de procesamiento en milisegundos
    """
    
    success: bool = Field(
        ...,
        description="Indica si el documento fue procesado exitosamente"
    )
    
    message: str = Field(
        ...,
        description="Mensaje descriptivo del resultado del procesamiento",
        example="Documento procesado e indexado exitosamente"
    )
    
    document: DocumentMetadata = Field(
        ...,
        description="Metadatos completos del documento procesado"
    )
    
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Tiempo total de procesamiento en milisegundos",
        ge=0,
        example=2500
    )


# ==================================================================================
#                           MODELOS DE SOLICITUD
# ==================================================================================

class DocumentSearchRequest(BaseModel):
    """
    Modelo para solicitudes de búsqueda de documentos.
    
    Permite especificar parámetros de búsqueda avanzada incluyendo
    filtros, ordenación y paginación.
    
    Attributes:
        query: Término de búsqueda
        limit: Número máximo de resultados
        offset: Número de resultados a omitir (paginación)
        filters: Filtros en formato Meilisearch
        sort: Campos de ordenación
    """
    
    query: str = Field(
        "",
        description="Término o frase a buscar (vacío para obtener todos)",
        max_length=500,
        example="contrato servicios"
    )
    
    limit: int = Field(
        20,
        description="Número máximo de resultados a devolver",
        ge=1,
        le=100,  # Máximo 100 resultados por página
        example=20
    )
    
    offset: int = Field(
        0,
        description="Número de resultados a omitir para paginación",
        ge=0,
        example=0
    )
    
    filters: Optional[str] = Field(
        default=None,
        description="Filtros en formato Meilisearch",
        example="file_extension = .pdf AND file_size_bytes > 100000"
    )
    
    sort: Optional[List[str]] = Field(
        default=None,
        description="Lista de campos de ordenación",
        example=["date:desc", "title:asc"]
    )


# ==================================================================================
#                           FUNCIONES AUXILIARES
# ==================================================================================

def create_document_metadata(
    document_id: str,
    filename: str,
    file_content: bytes,
    storage_path: str,
    ai_metadata: Dict[str, Any],
    media_type: str = "application/octet-stream"
) -> DocumentMetadata:
    """
    Función auxiliar para crear una instancia de DocumentMetadata.
    
    Combina información del archivo, metadatos de IA y datos de almacenamiento
    en un objeto DocumentMetadata válido.
    
    Args:
        document_id: ID único del documento
        filename: Nombre original del archivo
        file_content: Contenido del archivo en bytes
        storage_path: Ruta en Cloud Storage
        ai_metadata: Metadatos extraídos por IA
        media_type: Tipo MIME del archivo
        
    Returns:
        DocumentMetadata: Instancia válida con todos los metadatos
        
    Example:
        metadata = create_document_metadata(
            document_id="doc_123",
            filename="documento.pdf",
            file_content=pdf_bytes,
            storage_path="documents/2024/06/05/documento.pdf",
            ai_metadata={
                "title": "Mi Documento",
                "summary": "Resumen del contenido...",
                "keywords": ["palabra1", "palabra2"],
                "date": "2024-06-05"
            },
            media_type="application/pdf"
        )
    """
    import os
    from datetime import datetime
    
    # Extraer extensión del archivo
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Crear timestamp actual
    current_time = datetime.now().isoformat() + "Z"
    
    return DocumentMetadata(
        id=document_id,
        filename=filename,
        file_extension=file_extension,
        file_size_bytes=len(file_content),
        title=ai_metadata.get("title", "Título no disponible"),
        summary=ai_metadata.get("summary", "Resumen no disponible"),
        keywords=ai_metadata.get("keywords", []),
        date=ai_metadata.get("date", "Fecha no encontrada"),
        storage_path=storage_path,
        media_type=media_type,
        created_at=current_time,
        indexed_at=None  # Se establecerá después de la indexación
    )
