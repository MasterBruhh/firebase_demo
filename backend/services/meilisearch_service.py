"""
Servicio de Meilisearch - Motor de Búsqueda para Documentos

Este módulo gestiona toda la integración con Meilisearch, un motor de búsqueda
rápido y tolerante a errores tipográficos. Se encarga de:

- Inicialización y configuración del cliente Meilisearch
- Creación y gestión de índices de búsqueda
- Indexación de documentos y metadatos
- Operaciones de búsqueda con filtros y facetas
- Manejo robusto de errores de conectividad

Características principales:
- Búsqueda instantánea mientras escribes
- Tolerancia a errores tipográficos
- Soporte para múltiples idiomas
- Búsqueda por facetas y filtros
- Resultados ordenados por relevancia


"""

from typing import List, Dict, Any, Optional
from meilisearch import Client
from meilisearch.errors import MeilisearchError
from config import settings

# ==================================================================================
#                           CONFIGURACIÓN GLOBAL
# ==================================================================================

# Cliente global de Meilisearch (inicializado una sola vez)
client: Optional[Client] = None

# Nombre del índice principal para documentos
INDEX_NAME = "documents"

# Configuración del índice de documentos
INDEX_CONFIG = {
    "primaryKey": "id",                    # Campo único para cada documento
    "searchableAttributes": [             # Campos en los que se puede buscar
        "title",                          # Título del documento
        "summary",                        # Resumen generado por IA
        "keywords",                       # Palabras clave extraídas
        "filename",                       # Nombre del archivo original
        "text_content"                    # Contenido de texto (si está disponible)
    ],
    "filterableAttributes": [             # Campos que se pueden usar para filtrar
        "file_extension",                 # Extensión del archivo (.pdf, .docx, etc.)
        "file_size_bytes",               # Tamaño del archivo en bytes
        "date",                          # Fecha del documento
        "created_at",                    # Fecha de indexación
        "keywords"                       # Palabras clave (para filtros facetados)
    ],
    "sortableAttributes": [               # Campos por los que se puede ordenar
        "date",                          # Fecha del documento
        "created_at",                    # Fecha de indexación
        "file_size_bytes",               # Tamaño del archivo
        "title"                          # Título alfabéticamente
    ],
    "displayedAttributes": [             # Campos devueltos en los resultados
        "id",
        "title", 
        "summary",
        "keywords",
        "filename",
        "file_extension",
        "file_size_bytes",
        "date",
        "created_at"
    ]
}


# ==================================================================================
#                           FUNCIONES DE INICIALIZACIÓN
# ==================================================================================

def initialize_meilisearch() -> None:
    """
    Inicializa el cliente global de Meilisearch y configura el índice de documentos.
    
    Esta función se ejecuta al iniciar la aplicación y se encarga de:
    1. Crear la conexión con el servidor Meilisearch
    2. Verificar la conectividad y autenticación
    3. Crear el índice de documentos si no existe
    4. Configurar los atributos del índice (búsqueda, filtros, ordenación)
    
    Raises:
        RuntimeError: Si no se puede conectar a Meilisearch o la configuración es inválida
        MeilisearchError: Si hay errores específicos de Meilisearch
    """
    global client
    
    # Si ya está inicializado, no hacer nada
    if client is not None:
        # print("🔍 Meilisearch ya está inicializado")
        return

    try:
        # ===== CREAR CLIENTE DE MEILISEARCH =====
        client = Client(
            url=settings.MEILISEARCH_HOST,
            api_key=settings.MEILISEARCH_MASTER_KEY or None
        )
        
        # ===== VERIFICAR CONECTIVIDAD =====
        # Intentar obtener la lista de índices para verificar la conexión
        try:
            indices_response = client.get_indexes()
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo conectar a Meilisearch en {settings.MEILISEARCH_HOST}. "
                f"Verifica que el servidor esté ejecutándose y la configuración sea correcta. "
                f"Error: {exc}"
            ) from exc

        # ===== PROCESAR RESPUESTA DE ÍNDICES =====
        # Meilisearch puede devolver diferentes formatos según la versión
        if isinstance(indices_response, dict):
            # Formato con wrapper {"results": [...]}
            if "results" in indices_response:
                existing_indices = indices_response["results"]
            # Formato de error {"message": "...", "code": "..."}
            elif "message" in indices_response:
                raise RuntimeError(
                    f"Error de autenticación en Meilisearch: {indices_response['message']} "
                    f"(código: {indices_response.get('code', 'desconocido')}). "
                    f"Verifica la clave maestra MEILISEARCH_MASTER_KEY."
                )
            else:
                raise RuntimeError(f"Respuesta inesperada de Meilisearch: {indices_response}")
                
        elif isinstance(indices_response, list):
            # Formato directo como lista
            existing_indices = indices_response
        else:
            raise RuntimeError(f"Formato de respuesta desconocido: {type(indices_response)}")

        # ===== OBTENER NOMBRES DE ÍNDICES EXISTENTES =====
        existing_index_names = []
        for index_info in existing_indices:
            if isinstance(index_info, dict):
                # Objeto dict con información del índice
                existing_index_names.append(index_info.get("uid", ""))
            else:
                # Objeto con atributo uid
                existing_index_names.append(getattr(index_info, "uid", ""))

        # ===== CREAR ÍNDICE SI NO EXISTE =====
        if INDEX_NAME not in existing_index_names:
            # print(f"🔧 Creando índice '{INDEX_NAME}'...")
            
            # Crear índice con configuración inicial
            index_creation = client.create_index(
                uid=INDEX_NAME,
                options={"primaryKey": INDEX_CONFIG["primaryKey"]}
            )
            
            # Esperar a que se complete la creación del índice
            # (Meilisearch procesa esto de forma asíncrona)
            client.wait_for_task(index_creation.task_uid)
            
            # Configurar atributos del índice
            _configurar_indice()
            
            # print(f"✅ Índice '{INDEX_NAME}' creado y configurado")
        else:
            # El índice ya existe, verificar/actualizar configuración
            # print(f"📋 Índice '{INDEX_NAME}' ya existe, verificando configuración...")
            _configurar_indice()

        # print("✅ Meilisearch inicializado correctamente")

    except MeilisearchError as e:
        # Error específico de Meilisearch
        raise RuntimeError(
            f"Error de Meilisearch: {e.message if hasattr(e, 'message') else str(e)}. "
            f"Código: {e.code if hasattr(e, 'code') else 'desconocido'}"
        ) from e
    except Exception as e:
        # Error general
        raise RuntimeError(f"Error inesperado inicializando Meilisearch: {str(e)}") from e


def _configurar_indice() -> None:
    """
    Configura los atributos del índice de documentos.
    
    Esta función auxiliar aplica toda la configuración necesaria al índice:
    - Atributos en los que se puede buscar
    - Atributos que se pueden usar para filtrar
    - Atributos por los que se puede ordenar
    - Atributos que se devuelven en los resultados
    """
    if client is None:
        raise RuntimeError("Cliente de Meilisearch no inicializado")
    
    index = client.index(INDEX_NAME)
    
    try:
        # Configurar atributos de búsqueda
        task = index.update_searchable_attributes(INDEX_CONFIG["searchableAttributes"])
        client.wait_for_task(task.task_uid)
        
        # Configurar atributos filtrables
        task = index.update_filterable_attributes(INDEX_CONFIG["filterableAttributes"])
        client.wait_for_task(task.task_uid)
        
        # Configurar atributos ordenables
        task = index.update_sortable_attributes(INDEX_CONFIG["sortableAttributes"])
        client.wait_for_task(task.task_uid)
        
        # Configurar atributos mostrados
        task = index.update_displayed_attributes(INDEX_CONFIG["displayedAttributes"])
        client.wait_for_task(task.task_uid)
        
        # print(f"✅ Configuración del índice '{INDEX_NAME}' actualizada")
        
    except Exception as e:
        print(f"⚠️  Advertencia: No se pudo configurar el índice completamente: {e}")


def get_client() -> Client:
    """
    Obtiene el cliente global de Meilisearch.
    
    Returns:
        Client: Cliente autenticado de Meilisearch
        
    Raises:
        RuntimeError: Si el cliente no ha sido inicializado
    """
    if client is None:
        raise RuntimeError(
            "El cliente de Meilisearch no ha sido inicializado. "
            "Llama a initialize_meilisearch() primero."
        )
    return client


# ==================================================================================
#                           FUNCIONES DE INDEXACIÓN
# ==================================================================================

def add_documents(documents: List[Dict[str, Any]]) -> None:
    """
    Añade o actualiza documentos en el índice de Meilisearch.
    
    Esta función toma una lista de documentos con metadatos y los indexa
    para que puedan ser encontrados mediante búsquedas. Si un documento
    con el mismo ID ya existe, será actualizado.
    
    Args:
        documents: Lista de diccionarios con los metadatos de los documentos.
                  Cada documento debe tener al menos un campo 'id' único.
                  
    Ejemplo:
        documents = [
            {
                "id": "doc_123",
                "title": "Mi Documento",
                "summary": "Resumen del contenido...",
                "keywords": ["palabra1", "palabra2"],
                "filename": "documento.pdf",
                "file_extension": ".pdf",
                "file_size_bytes": 1024000,
                "date": "2024-01-15",
                "created_at": "2024-06-05T22:00:00Z"
            }
        ]
        
    Raises:
        RuntimeError: Si el cliente no está inicializado
        MeilisearchError: Si hay errores durante la indexación
    """
    # Asegurar que el cliente está inicializado
    initialize_meilisearch()
    
    if not documents:
        # print("⚠️  No hay documentos para indexar")
        return
    
    try:
        # Obtener el índice de documentos
        index = get_client().index(INDEX_NAME)
        
        # Añadir documentos al índice
        task = index.add_documents(documents)
        
        # Esperar a que se complete la indexación
        # (Opcional: quitar esto para operación asíncrona)
        get_client().wait_for_task(task.task_uid)
        
        # Mensaje de depuración - comentado para producción
        # print(f"✅ {len(documents)} documento(s) indexado(s) en Meilisearch")
        
    except MeilisearchError as e:
        raise RuntimeError(f"Error indexando documentos: {e.message if hasattr(e, 'message') else str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Error inesperado indexando documentos: {str(e)}") from e


def delete_document(document_id: str) -> None:
    """
    Elimina un documento específico del índice.
    
    Args:
        document_id: ID único del documento a eliminar
        
    Raises:
        RuntimeError: Si hay errores durante la eliminación
    """
    initialize_meilisearch()
    
    try:
        index = get_client().index(INDEX_NAME)
        task = index.delete_document(document_id)
        get_client().wait_for_task(task.task_uid)
        
        # print(f"✅ Documento '{document_id}' eliminado del índice")
        
    except Exception as e:
        raise RuntimeError(f"Error eliminando documento '{document_id}': {str(e)}") from e


# ==================================================================================
#                           FUNCIONES DE BÚSQUEDA
# ==================================================================================

def search_documents(
    query: str, 
    limit: int = 20,
    offset: int = 0,
    filters: Optional[str] = None,
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Realiza una búsqueda en el índice de documentos.
    
    Esta función proporciona capacidades avanzadas de búsqueda incluyendo:
    - Búsqueda de texto libre tolerante a errores
    - Filtros por atributos específicos
    - Ordenación personalizada
    - Paginación de resultados
    - Resaltado de términos encontrados
    
    Args:
        query: Término o frase a buscar. Puede estar vacío para obtener todos los documentos.
        limit: Número máximo de resultados a devolver (máximo 1000)
        offset: Número de resultados a omitir (para paginación)
        filters: Filtros en formato de Meilisearch (ej: "file_extension = .pdf")
        sort: Lista de campos por los que ordenar (ej: ["date:desc", "title:asc"])
        
    Returns:
        dict: Respuesta de Meilisearch con los resultados de la búsqueda
              - hits: Lista de documentos encontrados
              - query: Consulta original
              - processingTimeMs: Tiempo de procesamiento
              - limit: Límite aplicado
              - offset: Offset aplicado
              - estimatedTotalHits: Número estimado total de resultados
              
    Ejemplo:
        # Búsqueda simple
        resultados = search_documents("inteligencia artificial")
        
        # Búsqueda con filtros
        resultados = search_documents(
            query="contrato",
            filters="file_extension = .pdf AND file_size_bytes > 100000",
            sort=["date:desc"],
            limit=10
        )
        
    Raises:
        RuntimeError: Si hay errores durante la búsqueda
        ValueError: Si los parámetros son inválidos
    """
    # Validar parámetros
    if limit <= 0 or limit > 1000:
        raise ValueError("El límite debe estar entre 1 y 1000")
    if offset < 0:
        raise ValueError("El offset no puede ser negativo")
    
    # Asegurar que el cliente está inicializado
    initialize_meilisearch()
    
    try:
        # Construir opciones de búsqueda
        search_options = {
            "limit": limit,
            "offset": offset
        }
        
        # Añadir filtros si se proporcionan
        if filters:
            search_options["filter"] = filters
            
        # Añadir ordenación si se proporciona
        if sort:
            search_options["sort"] = sort
            
        # Configurar resaltado de términos
        search_options["attributesToHighlight"] = ["title", "summary"]
        search_options["highlightPreTag"] = "<mark>"
        search_options["highlightPostTag"] = "</mark>"
        
        # Realizar búsqueda
        index = get_client().index(INDEX_NAME)
        results = index.search(query, search_options)
        
        # Mensaje de depuración - comentado para producción
        # print(f"🔍 Búsqueda realizada: '{query}' -> {results.get('estimatedTotalHits', 0)} resultados")
        
        return results
        
    except MeilisearchError as e:
        raise RuntimeError(f"Error en la búsqueda: {e.message if hasattr(e, 'message') else str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Error inesperado en la búsqueda: {str(e)}") from e


def get_index_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas del índice de documentos.
    
    Returns:
        dict: Estadísticas del índice incluyendo:
              - numberOfDocuments: Número total de documentos indexados
              - isIndexing: Si el índice está procesando documentos
              - fieldDistribution: Distribución de campos
              
    Raises:
        RuntimeError: Si hay errores obteniendo las estadísticas
    """
    initialize_meilisearch()
    
    try:
        index = get_client().index(INDEX_NAME)
        stats = index.get_stats()
        
        # Añadir información adicional útil
        stats["index_name"] = INDEX_NAME
        stats["last_updated"] = "2024-06-05T22:00:00Z"  # En producción, usar timestamp real
        
        return stats
        
    except Exception as e:
        raise RuntimeError(f"Error obteniendo estadísticas del índice: {str(e)}") from e


# ==================================================================================
#                           FUNCIONES DE MANTENIMIENTO
# ==================================================================================

def clear_index() -> None:
    """
    Elimina todos los documentos del índice.
    
    ⚠️ ADVERTENCIA: Esta operación no se puede deshacer.
    Solo usar durante desarrollo o mantenimiento.
    
    Raises:
        RuntimeError: Si hay errores durante la operación
    """
    initialize_meilisearch()
    
    try:
        index = get_client().index(INDEX_NAME)
        task = index.delete_all_documents()
        get_client().wait_for_task(task.task_uid)
        
        print(f"⚠️  Todos los documentos han sido eliminados del índice '{INDEX_NAME}'")
        
    except Exception as e:
        raise RuntimeError(f"Error limpiando el índice: {str(e)}") from e


def reset_index() -> None:
    """
    Elimina y recrea completamente el índice.
    
    ⚠️ ADVERTENCIA: Esta operación elimina todos los datos y configuraciones.
    Solo usar durante desarrollo o para resolver problemas graves.
    
    Raises:
        RuntimeError: Si hay errores durante la operación
    """
    global client
    
    if client is None:
        raise RuntimeError("Cliente no inicializado")
    
    try:
        # Eliminar índice existente
        try:
            task = client.delete_index(INDEX_NAME)
            client.wait_for_task(task.task_uid)
            print(f"🗑️  Índice '{INDEX_NAME}' eliminado")
        except:
            # El índice puede no existir, continuar
            pass
        
        # Recrear índice
        task = client.create_index(
            uid=INDEX_NAME,
            options={"primaryKey": INDEX_CONFIG["primaryKey"]}
        )
        client.wait_for_task(task.task_uid)
        
        # Reconfigurar
        _configurar_indice()
        
        print(f"✅ Índice '{INDEX_NAME}' recreado y configurado")
        
    except Exception as e:
        raise RuntimeError(f"Error recreando el índice: {str(e)}") from e


# ==================================================================================
#                           SCRIPT DE PRUEBAS
# ==================================================================================

if __name__ == "__main__":
    """
    Script de pruebas para verificar la funcionalidad de Meilisearch.
    
    Ejecuta este archivo directamente para probar la conexión:
    python meilisearch_service.py
    """
    
    print("🔍 Probando conexión con Meilisearch...")
    print("=" * 50)
    
    try:
        # Inicializar cliente
        initialize_meilisearch()
        print("✅ Conexión establecida correctamente")
        
        # Obtener estadísticas
        stats = get_index_stats()
        print(f"📊 Documentos indexados: {stats.get('numberOfDocuments', 0)}")
        print(f"📊 Estado del índice: {'Indexando' if stats.get('isIndexing', False) else 'Listo'}")
        
        # Realizar búsqueda de prueba
        results = search_documents("", limit=5)
        print(f"🔍 Total de documentos disponibles: {results.get('estimatedTotalHits', 0)}")
        
        print("\n✅ Todas las pruebas pasaron exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        print("\n📖 Pasos para solucionar:")
        print("   1. Verifica que Meilisearch esté ejecutándose")
        print("   2. Confirma la URL en MEILISEARCH_HOST")
        print("   3. Verifica la clave maestra si es necesaria")
        print(f"   4. URL configurada: {settings.MEILISEARCH_HOST}")
        print(f"   5. Clave configurada: {'Sí' if settings.MEILISEARCH_MASTER_KEY else 'No'}")
