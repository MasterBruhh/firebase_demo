from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio # Necesario para ejecutar operaciones asíncronas

from config import settings
from services.firebase_service import initialize_firebase, get_firestore_client, get_auth_client
from services.meilisearch_service import initialize_meilisearch
from utils.audit_logger import log_event # Importamos el logger de auditoría
from routes import auth_routes, document_routes

# --- Contexto de vida de la aplicación (Startup/Shutdown) ---
# Usamos asynccontextmanager para manejar la inicialización y limpieza de recursos
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al iniciar y al cerrar la aplicación.
    Aquí inicializamos Firebase, Meilisearch, etc.
    """
    print("Iniciando la aplicación backend...")

    # 1. Inicializar Firebase Admin SDK
    try:
        initialize_firebase()
        # Puedes añadir aquí una verificación de conexión a Firestore si lo deseas
        firestore_client = get_firestore_client()
        # Intenta obtener una colección para verificar la conexión
        firestore_client.collection("health_check").document("test").set({"status": "ok"})
        print("Conexión a Firestore verificada.")
    except Exception as e:
        print(f"ERROR: No se pudo inicializar o conectar a Firebase: {e}")
        # Considera si quieres que la aplicación falle al iniciar si Firebase no está disponible
        # raise  # Descomenta esto para un fallo estricto

    # 2. Inicializar Meilisearch
    try:
        initialize_meilisearch()
        print("Meilisearch inicializado.")
    except Exception as e:
        print(f"ERROR: No se pudo inicializar o conectar a Meilisearch: {e}")
        # raise # Descomenta para un fallo estricto

    # 3. (Opcional) Crear un usuario admin inicial si no existe
    # ¡ADVERTENCIA! Este bloque solo debe usarse en desarrollo para la primera configuración.
    # EN PRODUCCIÓN, ELIMINALO O ASEGÚRATE DE UN PROCESO DE CREACIÓN DE ADMIN SEGURO.
    if settings.APP_ENV == "development":
        admin_email = "admin@example.com" # Puedes obtener esto de .env o pasarlo como argumento
        admin_password = "adminpassword" # ¡Cambia esto a una contraseña segura!
        try:
            # Verifica si el usuario ya existe para evitar errores
            user = None
            try:
                user = get_auth_client().get_user_by_email(admin_email)
            except Exception: # No existe el usuario
                pass

            if not user:
                # Crearlo y establecer custom claim de admin
                new_user = get_auth_client().create_user(email=admin_email, password=admin_password)
                get_auth_client().set_custom_user_claims(new_user.uid, {'admin': True})
                print(f"Usuario admin '{admin_email}' creado y marcado como admin.")
                print(f"IMPORTANTE: El usuario admin debe cerrar sesión y volver a iniciar sesión para que los custom claims tengan efecto.")
                # Registra el evento en la auditoría
                log_event(new_user.uid, 'ADMIN_USER_CREATED', {'email': admin_email})
            else:
                # Asegura que el usuario existente tenga el custom claim de admin
                user_claims = get_auth_client().get_user(user.uid).custom_claims
                if not user_claims or 'admin' not in user_claims or not user_claims['admin']:
                    get_auth_client().set_custom_user_claims(user.uid, {'admin': True})
                    print(f"Usuario '{admin_email}' ya existía, asegurado custom claim de admin.")
                    print(f"IMPORTANTE: El usuario admin debe cerrar sesión y volver a iniciar sesión para que los custom claims tengan efecto.")
                    log_event(user.uid, 'ADMIN_CLAIM_UPDATED', {'email': admin_email})
                else:
                    print(f"Usuario admin '{admin_email}' ya existe y está configurado.")

        except Exception as e:
            print(f"ADVERTENCIA: No se pudo crear/configurar el usuario admin inicial: {e}")


    yield # La aplicación está lista para recibir peticiones

    print("Cerrando la aplicación backend...")
    # Aquí puedes añadir código de limpieza si es necesario (ej. cerrar conexiones a BD)
    pass # No hay nada específico que cerrar para Firebase/Meilisearch clientes aquí

# --- Inicialización de la aplicación FastAPI ---
app = FastAPI(
    title="Gemini Indexer Demo Backend",
    description="API para subir, indexar y buscar documentos con Gemini y Meilisearch.",
    version="1.0.0",
    lifespan=lifespan # Conecta la función lifespan
)

# --- Configuración de CORS ---
# Esto es CRUCIAL para que tu frontend React pueda hacer peticiones a tu backend.
# En desarrollo, permitimos todo. En producción, especifica tus orígenes.
origins = [
    "http://localhost:3000",  # Origen de tu aplicación React en desarrollo
    "http://localhost:5173",  # Si usas Vite, este es el puerto común
    # "https://your-frontend-domain.com", # Agrega tu dominio de producción aquí
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Permite todos los headers
)

# --- Incluir Rutas ---
# Conectamos los enrutadores definidos en routes/
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(document_routes.router, prefix="/documents", tags=["Documents"])

# --- Ruta de Prueba ---
@app.get("/")
async def read_root():
    return {"message": "Bienvenido al backend del Indexador Gemini."}

# --- Manejo de Errores Global (Opcional, pero recomendado) ---
# Puedes añadir un manejador de excepciones global para errores no capturados
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log el error (puedes usar un logger más sofisticado aquí)
    print(f"Error no manejado: {exc}")
    # Puedes registrar el evento de error en Firestore también
    # log_event(None, 'GLOBAL_ERROR', {'error_message': str(exc), 'path': request.url.path})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Un error inesperado ha ocurrido.", "detail": str(exc)},
    )


# --- Ejecutar la aplicación (para desarrollo) ---
if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Ejecuta esto para iniciar el servidor de desarrollo
    # La parte para crear el admin inicial está ahora dentro del lifespan
    print("Para ejecutar el servidor, usa: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("O simplemente: python main.py si quieres ejecutarlo directamente (sin --reload)")

    # Para ejecutarlo directamente desde aquí (sin --reload)
    # asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000)) # Esto no funciona directamente así
    # Mejor usar el comando de uvicorn en la terminal.