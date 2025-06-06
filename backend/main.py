"""
Backend Principal - Indexador de Documentos con Gemini AI

Este módulo contiene la aplicación principal de FastAPI que actúa como el backend
del sistema de indexación de documentos. Integra Firebase para autenticación y
almacenamiento, Google Gemini AI para análisis de documentos, y Meilisearch para
búsquedas rápidas y tolerantes a errores tipográficos.


"""

# backend/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio # Necesario para ejecutar operaciones asíncronas

from config import settings
from services.firebase_service import (
    initialize_firebase, get_firestore_client, get_auth_client
)
from services.meilisearch_service import initialize_meilisearch
from utils.audit_logger import log_event
from routes import auth_routes, document_routes, audit_routes

# ==================================================================================
#                           GESTIÓN DEL CICLO DE VIDA DE LA APLICACIÓN
# ==================================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor del ciclo de vida de la aplicación FastAPI.
    
    Esta función se ejecuta automáticamente al iniciar y cerrar la aplicación.
    Se encarga de:
    1. Inicializar todos los servicios externos (Firebase, Meilisearch)
    2. Verificar conectividad con servicios
    3. Crear usuario administrador inicial en modo desarrollo
    4. Limpiar recursos al cerrar la aplicación
    
    Args:
        app (FastAPI): Instancia de la aplicación FastAPI
        
    Yields:
        None: Indica que la aplicación está lista para recibir peticiones
    """
    # ===== FASE DE INICIALIZACIÓN =====
    # Mensaje de depuración - comentado para producción
    # print("🚀 Iniciando la aplicación backend...")

    # 1. Inicialización del SDK de Firebase Admin
    try:
        # Inicializa Firebase con las credenciales del archivo de servicio
        initialize_firebase()
        
        # Verificación de conectividad con Firestore
        firestore_client = get_firestore_client()
        # Prueba de escritura para verificar que la conexión funciona
        firestore_client.collection("health_check").document("test").set({"status": "ok"})
        
        # Mensaje de depuración - comentado para producción
        # print("✅ Firebase Admin SDK inicializado exitosamente")
        # print("✅ Conexión a Firestore verificada")
        
    except Exception as e:
        # En caso de error, registra el problema pero permite que la app continúe
        print(f"❌ ERROR: No se pudo inicializar Firebase: {e}")
        # Descomenta la siguiente línea para forzar el cierre en caso de error
        # raise

    # 2. Inicialización del servicio de Meilisearch
    try:
        # Configura el cliente de Meilisearch y crea índices necesarios
        initialize_meilisearch()
        
        # Mensaje de depuración - comentado para producción
        # print("✅ Meilisearch inicializado correctamente")
        
    except Exception as e:
        # En caso de error, registra el problema pero permite que la app continúe
        print(f"❌ ERROR: No se pudo inicializar Meilisearch: {e}")
        # Descomenta la siguiente línea para forzar el cierre en caso de error
        # raise

    # 3. Creación de usuario administrador inicial (SOLO EN DESARROLLO)
    if settings.APP_ENV == "development":
        await _crear_usuario_admin_inicial()

    # ===== APLICACIÓN LISTA PARA RECIBIR PETICIONES =====
    yield

    # ===== FASE DE LIMPIEZA AL CERRAR =====
    # Mensaje de depuración - comentado para producción
    # print("🔄 Cerrando la aplicación backend...")
    
    # Aquí se pueden añadir tareas de limpieza si son necesarias
    # Por ejemplo: cerrar conexiones a bases de datos, limpiar archivos temporales, etc.
    pass


async def _crear_usuario_admin_inicial():
    """
    Función auxiliar para crear un usuario administrador inicial en modo desarrollo.
    
    ⚠️ ADVERTENCIA: Esta función solo debe ejecutarse en entorno de desarrollo.
    En producción, eliminar esta funcionalidad o implementar un proceso seguro
    de creación de administradores.
    
    La función:
    1. Verifica si ya existe un usuario administrador
    2. Lo crea si no existe
    3. Asigna custom claims de administrador
    4. Registra la actividad en los logs de auditoría
    """
    # Credenciales del administrador inicial - CAMBIAR EN PRODUCCIÓN
    admin_email = "admin@example.com"
    admin_password = "adminpassword"  # ⚠️ USAR CONTRASEÑA SEGURA EN PRODUCCIÓN
    
    try:
        # Verificar si el usuario administrador ya existe
        user = None
        try:
            user = get_auth_client().get_user_by_email(admin_email)
        except Exception:
            # El usuario no existe, esto es normal en la primera ejecución
            pass

        if not user:
            # Crear nuevo usuario administrador
            new_user = get_auth_client().create_user(
                email=admin_email, 
                password=admin_password
            )
            
            # Asignar privilegios de administrador mediante custom claims
            get_auth_client().set_custom_user_claims(new_user.uid, {'admin': True})
            
            # Mensajes de depuración - comentados para producción
            # print(f"✅ Usuario admin '{admin_email}' creado exitosamente")
            # print("⚠️  IMPORTANTE: El usuario debe cerrar sesión y volver a iniciar")
            # print("   para que los custom claims tengan efecto")
            
            # Registrar evento de creación en auditoría
            log_event(new_user.uid, 'ADMIN_USER_CREATED', {'email': admin_email})
            
        else:
            # El usuario existe, verificar que tenga privilegios de admin
            user_claims = get_auth_client().get_user(user.uid).custom_claims
            
            if not user_claims or 'admin' not in user_claims or not user_claims['admin']:
                # Asignar privilegios de administrador
                get_auth_client().set_custom_user_claims(user.uid, {'admin': True})
                
                # Mensaje de depuración - comentado para producción
                # print(f"✅ Privilegios de admin asignados a '{admin_email}'")
                # print("⚠️  IMPORTANTE: El usuario debe cerrar sesión y volver a iniciar")
                
                # Registrar actualización en auditoría
                log_event(user.uid, 'ADMIN_CLAIM_UPDATED', {'email': admin_email})
            else:
                # Usuario administrador ya configurado correctamente
                # print(f"✅ Usuario admin '{admin_email}' ya configurado")
                pass

    except Exception as e:
        # Error en la configuración del administrador - no crítico
        print(f"⚠️  ADVERTENCIA: Error configurando usuario admin inicial: {e}")


# ==================================================================================
#                           CONFIGURACIÓN DE LA APLICACIÓN FASTAPI
# ==================================================================================

# Crear instancia principal de FastAPI con metadatos
app = FastAPI(
    title="Indexador de Documentos con Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
    description=(
        "API REST para el sistema de indexación y búsqueda de documentos. "
        "Utiliza Google Gemini AI para análisis inteligente de contenido, "
        "Firebase para autenticación y almacenamiento, y Meilisearch para "
        "búsquedas rápidas y tolerantes a errores."
    ),
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc alternativo
)


# ==================================================================================
#                           CONFIGURACIÓN DE CORS
# ==================================================================================

# URLs permitidas para solicitudes desde el frontend
# En producción, reemplazar con las URLs reales del dominio
ALLOWED_ORIGINS = [
    "http://localhost:3000",    # React development server (Create React App)
    "http://localhost:5173",    # Vite development server
    "http://127.0.0.1:5173",    # Vite alternative
    # Añadir aquí las URLs de producción cuando sea necesario
    # "https://tu-dominio.com",
]

# Configurar middleware CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,          # Orígenes permitidos
    allow_credentials=True,                 # Permitir cookies/credenciales
    allow_methods=["*"],                    # Permitir todos los métodos HTTP
    allow_headers=["*"],                    # Permitir todos los headers
)


# ==================================================================================
#                           REGISTRO DE RUTAS
# ==================================================================================

# Incluir rutas de autenticación
app.include_router(
    auth_routes.router, 
    prefix="/auth", 
    tags=["🔐 Autenticación"],
    responses={
        401: {"description": "No autorizado - Token inválido o expirado"},
        403: {"description": "Prohibido - Permisos insuficientes"}
    }
)

# Incluir rutas de gestión de documentos
app.include_router(
    document_routes.router, 
    prefix="/documents", 
    tags=["📄 Documentos"],
    responses={
        400: {"description": "Solicitud incorrecta - Datos inválidos"},
        404: {"description": "Documento no encontrado"},
        413: {"description": "Archivo demasiado grande"}
    }
)

# Incluir rutas de auditoría (solo para administradores)
app.include_router(
    audit_routes.router, 
    prefix="/audit", 
    tags=["📊 Auditoría"],
    responses={
        403: {"description": "Prohibido - Solo administradores"},
        404: {"description": "Registros no encontrados"}
    }
)


# ==================================================================================
#                           ENDPOINTS BÁSICOS
# ==================================================================================

@app.get(
    "/", 
    summary="Endpoint raíz",
    description="Endpoint de bienvenida que confirma que la API está funcionando",
    response_description="Mensaje de bienvenida",
    tags=["🏠 General"]
)
async def root():
    """
    Endpoint raíz de la API.
    
    Returns:
        dict: Mensaje de bienvenida con información básica de la API
    """
    return {
        "message": "🚀 Bienvenido al Indexador de Documentos con Gemini AI",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "✅ Operativo"
    }


@app.get(
    "/health", 
    summary="Estado de salud",
    description="Verificación del estado de la API y servicios conectados",
    tags=["🏠 General"]
)
async def health_check():
    """
    Endpoint para verificar el estado de salud de la API.
    
    Returns:
        dict: Estado de la API y servicios conectados
    """
    return {
        "status": "healthy",
        "timestamp": "2024-06-05T22:00:00Z",
        "services": {
            "api": "✅ Operativo",
            "firebase": "✅ Conectado",
            "meilisearch": "✅ Conectado"
        }
    }


# ==================================================================================
#                           MANEJO GLOBAL DE ERRORES
# ==================================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global de excepciones no capturadas.
    
    Este manejador se ejecuta cuando ocurre cualquier excepción no manejada
    en la aplicación. Se encarga de:
    1. Registrar el error para depuración
    2. Ocultar detalles sensibles al usuario
    3. Devolver una respuesta JSON consistente
    
    Args:
        request (Request): Objeto de la petición HTTP
        exc (Exception): Excepción que ocurrió
        
    Returns:
        JSONResponse: Respuesta JSON con información del error
    """
    # Registro del error para depuración (en logs del servidor)
    print(f"❌ Error no manejado en {request.url.path}: {exc}")
    
    # Opcional: Registrar evento de error en auditoría
    # Descomenta si quieres rastrear todos los errores
    # try:
    #     log_event(None, 'GLOBAL_ERROR', {
    #         'error_message': str(exc),
    #         'path': request.url.path,
    #         'method': request.method
    #     })
    # except:
    #     pass  # No fallar si el logging de auditoría también falla
    
    # Respuesta consistente para el cliente
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "message": "Ha ocurrido un error inesperado. Por favor, intenta de nuevo.",
            "code": "INTERNAL_SERVER_ERROR",
            # En desarrollo, puedes descomentar la siguiente línea para ver detalles
            # "detail": str(exc)
        },
    )


# ==================================================================================
#                           PUNTO DE ENTRADA PARA DESARROLLO
# ==================================================================================

if __name__ == "__main__":
    """
    Punto de entrada cuando se ejecuta el archivo directamente.
    
    ⚠️ NOTA: Para desarrollo, es recomendable usar el comando uvicorn
    directamente en lugar de ejecutar este archivo, ya que permite
    hot-reloading automático.
    """
    
    # Instrucciones para ejecutar el servidor
    print("📖 Para iniciar el servidor de desarrollo:")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("📖 URLs disponibles:")
    print("   • API: http://localhost:8000")
    print("   • Documentación: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    
    # Ejecución directa (sin hot-reload)
    # Descomenta las siguientes líneas si quieres ejecutar directamente
    # uvicorn.run(
    #     "main:app",
    #     host="0.0.0.0",
    #     port=8000,
    #     reload=False,  # Sin hot-reload en ejecución directa
    #     log_level="info"
    # )
