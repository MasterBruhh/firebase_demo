import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from config import settings # Importa las configuraciones
import os

# Inicializar Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps: # Evita inicializar múltiples veces
        try:
            # Asegúrate de que la ruta al archivo de cuenta de servicio es correcta
            # La ruta de settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH debe ser absoluta o relativa a donde se ejecuta el script.
            # Para simplificar, asumimos que config.py está en la misma raíz que main.py y el JSON
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Llega a indexador-demo/backend
            service_account_path = os.path.join(base_path, settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)

            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Firebase service account file not found at: {service_account_path}")

            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_STORAGE_BUCKET
            })
            print("Firebase Admin SDK inicializado exitosamente.")
        except Exception as e:
            print(f"Error al inicializar Firebase Admin SDK: {e}")
            raise

# Funciones para obtener los clientes de los servicios
def get_firestore_client():
    initialize_firebase() # Asegura que Firebase esté inicializado
    return firestore.client()

def get_auth_client():
    initialize_firebase()
    return auth

def get_storage_client():
    initialize_firebase()
    return storage.bucket()

# Pequeña función para probar la autenticación
async def create_admin_user(email: str, password: str):
    try:
        user = get_auth_client().create_user(
            email=email,
            password=password
        )
        # Opcional: Establecer un custom claim para identificar al admin
        get_auth_client().set_custom_user_claims(user.uid, {'admin': True})
        print(f"Usuario admin '{email}' creado exitosamente con UID: {user.uid}")
        return user
    except Exception as e:
        print(f"Error al crear usuario admin: {e}")
        raise

# Ejemplo de cómo usarlo para crear un admin inicial (solo para desarrollo/primer uso)
# No lo incluyas en la ejecución normal de tu API, es solo para configuración
if __name__ == "__main__":
    import asyncio
    # Solo para probar la creación del admin en el primer setup
    # BORRA ESTO O COMENTALO UNA VEZ QUE HAYAS CREADO TU ADMIN
    async def setup_initial_admin():
        admin_email = input("Introduce el email para el usuario admin: ")
        admin_password = input("Introduce la contraseña para el usuario admin: ")
        try:
            await create_admin_user(admin_email, admin_password)
        except Exception as e:
            print(f"Fallo la creación del admin: {e}")

    asyncio.run(setup_initial_admin())