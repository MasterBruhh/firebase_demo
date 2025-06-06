"""
Servicio de Firebase - Integración con Firebase Admin SDK

Este módulo maneja toda la integración con los servicios de Firebase, incluyendo:

- Firebase Authentication (autenticación de usuarios)
- Cloud Firestore (base de datos NoSQL)
- Cloud Storage (almacenamiento de archivos)
- Administración de usuarios y roles

Servicios integrados:
- Authentication: Gestión de usuarios, tokens JWT, custom claims
- Firestore: Base de datos NoSQL para metadatos y auditoría
- Storage: Almacenamiento seguro de documentos con organización por fechas


"""

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from firebase_admin.exceptions import FirebaseError
from config import settings
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# ==================================================================================
#                           INICIALIZACIÓN DE FIREBASE
# ==================================================================================

def initialize_firebase() -> None:
    """
    Inicializa el SDK de Firebase Admin con las credenciales del proyecto.
    
    Esta función se ejecuta una sola vez al iniciar la aplicación y configura:
    1. Las credenciales de la cuenta de servicio
    2. La configuración del bucket de Storage
    3. La conexión con todos los servicios de Firebase
    
    La inicialización es segura para múltiples llamadas - solo se ejecuta una vez.
    
    Raises:
        FileNotFoundError: Si no se encuentra el archivo de credenciales
        FirebaseError: Si hay errores en la configuración de Firebase
        Exception: Si hay otros errores durante la inicialización
    """
    # Verificar si Firebase ya está inicializado
    if firebase_admin._apps:
        # print("🔥 Firebase ya está inicializado")
        return

    try:
        # ===== CONSTRUIR RUTA AL ARCHIVO DE CREDENCIALES =====
        # Obtener el directorio padre del directorio actual (backend/)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        service_account_path = os.path.join(base_path, settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)

        # Verificar que el archivo existe
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Archivo de credenciales de Firebase no encontrado en: {service_account_path}\n"
                f"Asegúrate de que:\n"
                f"  1. El archivo existe en la ubicación especificada\n"
                f"  2. La variable FIREBASE_SERVICE_ACCOUNT_KEY_PATH en .env es correcta\n"
                f"  3. Tienes permisos de lectura sobre el archivo"
            )

        # ===== CARGAR CREDENCIALES Y CONFIGURAR FIREBASE =====
        # Crear objeto de credenciales desde el archivo JSON
        cred = credentials.Certificate(service_account_path)
        
        # Inicializar Firebase Admin SDK con configuración
        firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })
        
        # Mensaje de depuración - comentado para producción
        # print("✅ Firebase Admin SDK inicializado exitosamente")
        
    except FileNotFoundError:
        # Re-lanzar FileNotFoundError tal como está
        raise
    except FirebaseError as e:
        # Error específico de Firebase
        raise FirebaseError(
            f"Error configurando Firebase: {e}. "
            f"Verifica que:\n"
            f"  1. Las credenciales son válidas\n"
            f"  2. El proyecto Firebase existe\n"
            f"  3. Los servicios están habilitados"
        )
    except Exception as e:
        # Error general
        raise Exception(f"Error inesperado inicializando Firebase: {e}")


# ==================================================================================
#                           FUNCIONES DE ACCESO A SERVICIOS
# ==================================================================================

def get_firestore_client():
    """
    Obtiene un cliente autenticado para Cloud Firestore.
    
    Firestore es la base de datos NoSQL de Firebase. Se utiliza para:
    - Almacenar metadatos de documentos
    - Registros de auditoría
    - Configuraciones de la aplicación
    - Datos de usuarios
    
    Returns:
        firestore.Client: Cliente autenticado de Firestore
        
    Example:
        db = get_firestore_client()
        doc_ref = db.collection('documents').document('doc_id')
        doc_ref.set({'title': 'Mi documento'})
    """
    initialize_firebase()
    return firestore.client()


def get_auth_client():
    """
    Obtiene un cliente autenticado para Firebase Authentication.
    
    Firebase Auth se utiliza para:
    - Verificar tokens JWT
    - Gestionar usuarios
    - Asignar roles mediante custom claims
    - Validar permisos
    
    Returns:
        auth: Cliente de Firebase Authentication
        
    Example:
        auth_client = get_auth_client()
        user = auth_client.get_user(uid)
        auth_client.set_custom_user_claims(uid, {'admin': True})
    """
    initialize_firebase()
    return auth


def get_storage_bucket():
    """
    Obtiene una referencia al bucket de Cloud Storage.
    
    Cloud Storage se utiliza para:
    - Almacenar archivos de documentos
    - Organizar archivos por fecha
    - Controlar acceso a archivos
    - Generar URLs de descarga
    
    Returns:
        storage.Bucket: Referencia al bucket de Storage
        
    Example:
        bucket = get_storage_bucket()
        blob = bucket.blob('ruta/archivo.pdf')
        blob.upload_from_string(data)
    """
    initialize_firebase()
    return storage.bucket()


# ==================================================================================
#                           FUNCIONES DE GESTIÓN DE ARCHIVOS
# ==================================================================================

def _dated_blob_path(filename: str) -> str:
    """
    Genera una ruta organizada por fecha para almacenar archivos.
    
    Crea una estructura jerárquica basada en la fecha actual:
    documents/YYYY/MM/DD/filename
    
    Esta organización permite:
    - Fácil navegación temporal
    - Distribución equilibrada de archivos
    - Búsqueda eficiente por fechas
    - Mantenimiento y limpieza organizados
    
    Args:
        filename: Nombre del archivo original
        
    Returns:
        str: Ruta completa con estructura de fechas
        
    Example:
        path = _dated_blob_path("documento.pdf")
        # Resultado: "documents/2024/06/05/documento.pdf"
    """
    today = datetime.now()
    return (
        f"documents/"
        f"{today.year:04d}/"      # Año con 4 dígitos
        f"{today.month:02d}/"     # Mes con cero a la izquierda
        f"{today.day:02d}/"       # Día con cero a la izquierda
        f"{filename}"
    )


def upload_file_to_storage(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> str:
    """
    Sube un archivo a Cloud Storage con organización automática por fechas.
    
    Esta función:
    1. Organiza el archivo en una estructura de fechas
    2. Sube el contenido al bucket configurado
    3. Establece el tipo de contenido apropiado
    4. Devuelve la ruta del archivo para referencias futuras
    
    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre original del archivo
        content_type: Tipo MIME del archivo (se detecta automáticamente si no se especifica)
        
    Returns:
        str: Ruta interna del archivo en Storage (blob path)
        
    Example:
        with open('documento.pdf', 'rb') as f:
            blob_path = upload_file_to_storage(
                file_bytes=f.read(),
                filename='documento.pdf',
                content_type='application/pdf'
            )
        # blob_path: "documents/2024/06/05/documento.pdf"
        
    Raises:
        Exception: Si hay errores durante la subida
    """
    try:
        # Obtener referencia al bucket
        bucket = get_storage_bucket()
        
        # Generar ruta con estructura de fechas
        blob_path = _dated_blob_path(filename)
        
        # Crear referencia al archivo en Storage
        blob = bucket.blob(blob_path)
        
        # Subir el archivo con el tipo de contenido especificado
        blob.upload_from_string(file_bytes, content_type=content_type)
        
        # Mensaje de depuración - comentado para producción
        # print(f"✅ Archivo '{filename}' subido a Storage → {blob_path}")
        
        return blob_path
        
    except Exception as e:
        raise Exception(f"Error subiendo archivo '{filename}' a Storage: {e}")


def download_file_from_storage(blob_path: str) -> bytes:
    """
    Descarga un archivo desde Cloud Storage.
    
    Args:
        blob_path: Ruta interna del archivo en Storage
        
    Returns:
        bytes: Contenido del archivo en bytes
        
    Example:
        file_content = download_file_from_storage("documents/2024/06/05/documento.pdf")
        with open('descargado.pdf', 'wb') as f:
            f.write(file_content)
            
    Raises:
        Exception: Si el archivo no existe o hay errores de descarga
    """
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(blob_path)
        
        # Verificar que el archivo existe
        if not blob.exists():
            raise FileNotFoundError(f"Archivo no encontrado en Storage: {blob_path}")
        
        return blob.download_as_bytes()
        
    except FileNotFoundError:
        # Re-lanzar FileNotFoundError tal como está
        raise
    except Exception as e:
        raise Exception(f"Error descargando archivo desde Storage: {e}")


def list_files_in_storage(prefix: str = "documents/") -> List[Dict[str, Any]]:
    """
    Lista archivos en Cloud Storage con metadatos.
    
    Args:
        prefix: Prefijo para filtrar archivos (por defecto "documents/")
        
    Returns:
        List[Dict]: Lista de diccionarios con información de cada archivo:
                   - path: Ruta completa del archivo
                   - filename: Nombre del archivo sin ruta
                   - size: Tamaño en bytes
                   - updated: Fecha de última modificación (ISO format)
                   - content_type: Tipo MIME del archivo
                   
    Example:
        files = list_files_in_storage("documents/2024/06/")
        for file_info in files:
            print(f"Archivo: {file_info['filename']}, Tamaño: {file_info['size']} bytes")
            
    Raises:
        Exception: Si hay errores accediendo a Storage
    """
    try:
        bucket = get_storage_bucket()
        files = []
        
        # Iterar sobre todos los blobs con el prefijo especificado
        for blob in bucket.list_blobs(prefix=prefix):
            # Ignorar "directorios" (rutas que terminan con /)
            if blob.name.endswith("/"):
                continue
                
            # Construir información del archivo
            file_info = {
                "path": blob.name,
                "filename": os.path.basename(blob.name),
                "size": blob.size or 0,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type or "application/octet-stream"
            }
            files.append(file_info)
        
        return files
        
    except Exception as e:
        raise Exception(f"Error listando archivos en Storage: {e}")


def delete_file_from_storage(blob_path: str) -> None:
    """
    Elimina un archivo de Cloud Storage.
    
    Args:
        blob_path: Ruta interna del archivo en Storage
        
    Raises:
        Exception: Si hay errores durante la eliminación
    """
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(blob_path)
        
        # Verificar que el archivo existe antes de eliminarlo
        if not blob.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {blob_path}")
        
        blob.delete()
        
        # Mensaje de depuración - comentado para producción
        # print(f"🗑️ Archivo eliminado de Storage: {blob_path}")
        
    except FileNotFoundError:
        # Re-lanzar FileNotFoundError tal como está
        raise
    except Exception as e:
        raise Exception(f"Error eliminando archivo de Storage: {e}")


# ==================================================================================
#                           FUNCIONES DE GESTIÓN DE USUARIOS
# ==================================================================================

async def create_admin_user(email: str, password: str) -> Dict[str, Any]:
    """
    Crea un usuario administrador con privilegios especiales.
    
    ⚠️ ADVERTENCIA: Esta función es para desarrollo inicial únicamente.
    En producción, implementar un proceso seguro de creación de administradores.
    
    Args:
        email: Correo electrónico del administrador
        password: Contraseña del administrador
        
    Returns:
        Dict: Información del usuario creado
        
    Raises:
        Exception: Si hay errores durante la creación
    """
    try:
        auth_client = get_auth_client()
        
        # Crear usuario con email y contraseña
        user = auth_client.create_user(
            email=email,
            password=password,
            email_verified=True  # Marcar email como verificado
        )
        
        # Asignar custom claim de administrador
        auth_client.set_custom_user_claims(user.uid, {'admin': True})
        
        # Mensaje de depuración - comentado para producción
        # print(f"✅ Usuario admin '{email}' creado con UID: {user.uid}")
        # print("⚠️  IMPORTANTE: El usuario debe cerrar sesión y volver a iniciar")
        # print("   para que los custom claims tengan efecto")
        
        return {
            "uid": user.uid,
            "email": email,
            "admin": True,
            "created_at": datetime.now().isoformat()
        }
        
    except FirebaseError as e:
        if "EMAIL_EXISTS" in str(e):
            raise Exception(f"El email '{email}' ya está registrado en Firebase")
        else:
            raise Exception(f"Error de Firebase creando usuario admin: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado creando usuario admin: {e}")


def get_user_info(uid: str) -> Dict[str, Any]:
    """
    Obtiene información completa de un usuario por su UID.
    
    Args:
        uid: ID único del usuario
        
    Returns:
        Dict: Información del usuario incluyendo custom claims
        
    Raises:
        Exception: Si el usuario no existe o hay errores
    """
    try:
        auth_client = get_auth_client()
        user = auth_client.get_user(uid)
        
        return {
            "uid": user.uid,
            "email": user.email,
            "email_verified": user.email_verified,
            "disabled": user.disabled,
            "custom_claims": user.custom_claims or {},
            "creation_time": user.user_metadata.creation_timestamp,
            "last_sign_in": user.user_metadata.last_sign_in_timestamp
        }
        
    except FirebaseError as e:
        if "USER_NOT_FOUND" in str(e):
            raise Exception(f"Usuario no encontrado: {uid}")
        else:
            raise Exception(f"Error obteniendo información del usuario: {e}")


# ==================================================================================
#                           SCRIPT DE DESARROLLO
# ==================================================================================

if __name__ == "__main__":
    """
    Script de desarrollo para crear un administrador inicial.
    
    ⚠️ ADVERTENCIA: Este script es solo para desarrollo inicial.
    En producción, comentar o eliminar esta sección.
    
    Ejecuta: python firebase_service.py
    """
    import asyncio
    
    async def setup_initial_admin():
        """
        Función interactiva para crear un administrador inicial.
        """
        print("🔥 Configuración inicial de administrador Firebase")
        print("=" * 50)
        print("⚠️  Solo usar en desarrollo inicial")
        print()
        
        try:
            # Solicitar credenciales del administrador
            admin_email = input("📧 Email del administrador: ").strip()
            admin_password = input("🔐 Contraseña del administrador: ").strip()
            
            # Validaciones básicas
            if not admin_email or "@" not in admin_email:
                print("❌ Email inválido")
                return
                
            if len(admin_password) < 6:
                print("❌ La contraseña debe tener al menos 6 caracteres")
                return
            
            # Crear usuario administrador
            user_info = await create_admin_user(admin_email, admin_password)
            
            print(f"✅ Usuario admin creado exitosamente:")
            print(f"   📧 Email: {user_info['email']}")
            print(f"   🆔 UID: {user_info['uid']}")
            print()
            print("⚠️  IMPORTANTE:")
            print("   1. Cambia la contraseña desde la aplicación")
            print("   2. El usuario debe cerrar sesión y volver a iniciar")
            print("   3. Comenta este script en producción")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Ejecutar solo si se llama directamente
    # En producción, comentar la siguiente línea:
    # asyncio.run(setup_initial_admin())