# indexador-demo/backend/services/meilisearch_service.py

from meilisearch import Client
from config import settings # Asumiendo que las configuraciones están accesibles

meilisearch_client: Client = None

def initialize_meilisearch():
    """
    Inicializa el cliente de Meilisearch.
    """
    global meilisearch_client
    if meilisearch_client is None:
        try:
            meilisearch_client = Client(settings.MEILISEARCH_HOST, settings.MEILISEARCH_MASTER_KEY)
            # Opcional: Intenta obtener la versión para verificar la conexión
            version = meilisearch_client.get_version()
            print(f"Meilisearch inicializado exitosamente. Versión: {version['pkgVersion']}")
        except Exception as e:
            print(f"Error al inicializar Meilisearch: {e}")
            raise # Propaga la excepción para que el inicio de la app falle si Meilisearch no está disponible

def get_meilisearch_client() -> Client:
    """
    Retorna la instancia del cliente de Meilisearch inicializada.
    """
    if meilisearch_client is None:
        raise Exception("Meilisearch client not initialized. Call initialize_meilisearch() first.")
    return meilisearch_client

# Funciones placeholder para futuras implementaciones
async def add_documents_to_meilisearch(index_name: str, documents: list):
    """
    Añade o actualiza documentos en un índice de Meilisearch.
    """
    client = get_meilisearch_client()
    # await client.index(index_name).add_documents(documents) # Implementaremos esto más tarde
    print(f"Simulando añadir {len(documents)} documentos al índice '{index_name}' en Meilisearch.")
    pass

async def search_documents_in_meilisearch(index_name: str, query: str):
    """
    Busca documentos en un índice de Meilisearch.
    """
    client = get_meilisearch_client()
    # results = await client.index(index_name).search(query) # Implementaremos esto más tarde
    print(f"Simulando búsqueda de '{query}' en el índice '{index_name}' en Meilisearch.")
    return {"hits": [], "query": query} # Retorna un resultado vacío por ahora