"""
Configuración de la Aplicación - Indexador de Documentos con Gemini AI

Este módulo maneja toda la configuración de la aplicación utilizando Pydantic
para validación automática de variables de entorno. Se encarga de cargar y
validar todas las credenciales y configuraciones necesarias para:

- Firebase (autenticación, Firestore, Storage)
- Google Gemini AI (análisis de documentos)
- Meilisearch (motor de búsqueda)
- Configuraciones de seguridad y entorno


"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

# ==================================================================================
#                           CONFIGURACIÓN DE RUTAS DE ARCHIVOS
# ==================================================================================

# Determinar la ruta base del proyecto (directorio donde está este archivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construir la ruta al archivo .env (debe estar en el mismo directorio que config.py)
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")


# ==================================================================================
#                           CLASE DE CONFIGURACIÓN PRINCIPAL
# ==================================================================================

class Settings(BaseSettings):
    """
    Clase de configuración principal utilizando Pydantic Settings.
    
    Esta clase define todas las variables de configuración necesarias para la aplicación.
    Pydantic se encarga automáticamente de:
    - Cargar variables desde el archivo .env
    - Validar tipos de datos
    - Proporcionar valores por defecto
    - Generar errores descriptivos si faltan variables requeridas
    
    Attributes:
        model_config: Configuración del modelo Pydantic
        FIREBASE_SERVICE_ACCOUNT_KEY_PATH: Ruta al archivo JSON de credenciales de Firebase
        FIREBASE_STORAGE_BUCKET: Nombre del bucket de Firebase Storage
        GEMINI_API_KEY: Clave de API para Google Gemini AI
        MEILISEARCH_HOST: URL del servidor Meilisearch
        MEILISEARCH_MASTER_KEY: Clave maestra de Meilisearch (opcional)
        SECRET_KEY: Clave secreta para JWT y otras funciones de seguridad
        APP_ENV: Entorno de la aplicación (development, production)
    """
    
    # Configuración del modelo Pydantic
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,        # Archivo de variables de entorno
        env_file_encoding='utf-8',     # Codificación del archivo .env
        extra='ignore'                 # Ignorar variables no definidas aquí
    )

    # ===== CONFIGURACIÓN DE FIREBASE =====
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = Field(
        ...,  # Campo requerido
        description="Ruta relativa o absoluta al archivo JSON de credenciales de Firebase Service Account",
        example="firebase-service-account.json"
    )
    
    FIREBASE_STORAGE_BUCKET: str = Field(
        ...,  # Campo requerido
        description="Nombre del bucket de Firebase Storage para almacenar documentos",
        example="mi-proyecto.appspot.com"
    )

    # ===== CONFIGURACIÓN DE GOOGLE GEMINI AI =====
    GEMINI_API_KEY: str = Field(
        ...,  # Campo requerido
        description="Clave de API de Google Gemini para análisis de documentos con IA",
        min_length=20  # Validación mínima de longitud
    )

    # ===== CONFIGURACIÓN DE MEILISEARCH =====
    MEILISEARCH_HOST: str = Field(
        ...,  # Campo requerido
        description="URL completa del servidor Meilisearch",
        example="http://localhost:7700"
    )
    
    MEILISEARCH_MASTER_KEY: str | None = Field(
        None,  # Campo opcional
        description="Clave maestra de Meilisearch para autenticación (opcional en desarrollo)",
        min_length=16  # Si se proporciona, debe tener al menos 16 caracteres
    )

    # ===== CONFIGURACIÓN DE SEGURIDAD =====
    SECRET_KEY: str = Field(
        ...,  # Campo requerido
        description="Clave secreta para JWT y otras funciones criptográficas",
        min_length=32  # Mínimo 32 caracteres para seguridad
    )

    # ===== CONFIGURACIÓN DEL ENTORNO =====
    APP_ENV: str = Field(
        "development",                                           # valor por defecto
        description="Entorno de la aplicación: development, staging, production",
        pattern=r"^(development|staging|production)$"            # ← antes era regex=
    )


# ==================================================================================
#                           INSTANCIA GLOBAL DE CONFIGURACIÓN
# ==================================================================================

# Crear una instancia única de configuración para importar en otros módulos
# Esta instancia carga automáticamente todas las variables del archivo .env
try:
    settings = Settings()
    
    # Mensaje de depuración - comentado para producción
    # print("✅ Configuración cargada exitosamente")
    
except Exception as e:
    # Error crítico: la aplicación no puede funcionar sin configuración válida
    print(f"❌ ERROR CRÍTICO: No se pudo cargar la configuración: {e}")
    print("📋 Asegúrate de que:")
    print("   1. El archivo .env existe en el directorio backend/")
    print("   2. Todas las variables requeridas están definidas")
    print("   3. Los valores tienen el formato correcto")
    print("📖 Consulta la documentación para más detalles")
    raise


# ==================================================================================
#                           FUNCIÓN DE VALIDACIÓN PARA DESARROLLO
# ==================================================================================

def validar_configuracion():
    """
    Función auxiliar para validar que todas las configuraciones están correctas.
    
    Útil para ejecutar durante el desarrollo para verificar que todos los
    servicios externos están configurados correctamente.
    
    Returns:
        bool: True si toda la configuración es válida
        
    Raises:
        ValueError: Si alguna configuración es inválida
    """
    errores = []
    
    # Validar archivo de credenciales de Firebase
    firebase_path = os.path.join(BASE_DIR, settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
    if not os.path.exists(firebase_path):
        errores.append(f"Archivo de credenciales Firebase no encontrado: {firebase_path}")
    
    # Validar formato del bucket de Storage
    if not settings.FIREBASE_STORAGE_BUCKET.endswith('.appspot.com'):
        errores.append("El bucket de Firebase Storage debe terminar en '.appspot.com'")
    
    # Validar formato de la URL de Meilisearch
    if not settings.MEILISEARCH_HOST.startswith(('http://', 'https://')):
        errores.append("MEILISEARCH_HOST debe ser una URL completa (http:// o https://)")
    
    # Validar longitud de la clave secreta
    if len(settings.SECRET_KEY) < 32:
        errores.append("SECRET_KEY debe tener al menos 32 caracteres")
    
    if errores:
        raise ValueError("Errores de configuración encontrados:\n" + "\n".join(f"  • {error}" for error in errores))
    
    return True


# ==================================================================================
#                           SCRIPT DE DEPURACIÓN
# ==================================================================================

if __name__ == "__main__":
    """
    Script de depuración para verificar la configuración.
    
    Ejecuta este archivo directamente para ver el estado de la configuración:
    python config.py
    """
    
    print("🔍 Verificando configuración de la aplicación...")
    print("=" * 60)
    
    try:
        # Intentar validar toda la configuración
        validar_configuracion()
        
        print("📋 Configuraciones cargadas:")
        print(f"   • Archivo de credenciales Firebase: {settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
        print(f"   • Bucket de Storage: {settings.FIREBASE_STORAGE_BUCKET}")
        print(f"   • Clave Gemini API: {settings.GEMINI_API_KEY[:8]}..." if settings.GEMINI_API_KEY else "   • Clave Gemini API: NO CONFIGURADA")
        print(f"   • Host Meilisearch: {settings.MEILISEARCH_HOST}")
        print(f"   • Clave Meilisearch: {'✅ Configurada' if settings.MEILISEARCH_MASTER_KEY else '⚠️  No configurada (opcional)'}")
        print(f"   • Clave secreta: {'✅ Configurada' if settings.SECRET_KEY else '❌ No configurada'}")
        print(f"   • Entorno: {settings.APP_ENV}")
        
        print("\n✅ Configuración válida - La aplicación puede iniciarse")
        
    except Exception as e:
        print(f"\n❌ Error en la configuración: {e}")
        print("\n📖 Pasos para solucionar:")
        print("   1. Crea un archivo .env en el directorio backend/")
        print("   2. Añade todas las variables requeridas")
        print("   3. Verifica que los archivos de credenciales existen")
        print("   4. Ejecuta este script nuevamente para verificar")
        
        # Ejemplo de archivo .env para referencia
        print("\n📄 Ejemplo de archivo .env:")
        print("""
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=firebase-service-account.json
FIREBASE_STORAGE_BUCKET=tu-proyecto.appspot.com

# Google Gemini AI
GEMINI_API_KEY=tu-clave-de-gemini-aqui

# Meilisearch Configuration
MEILISEARCH_HOST=http://localhost:7700
MEILISEARCH_MASTER_KEY=tu-clave-meilisearch-aqui

# Security
SECRET_KEY=una-clave-muy-segura-de-al-menos-32-caracteres

# Environment
APP_ENV=development
        """.strip())
