# indexador-demo/backend/routes/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Para manejar tokens en headers
from services.auth_service import register_user, verify_id_token, UserRegister, TokenData
from utils.audit_logger import log_event
from typing import Annotated

router = APIRouter()

# OAuth2PasswordBearer para extraer el token del header Authorization
# No se usa para el login, sino para proteger otras rutas que requieran autenticación.
# El 'tokenUrl' es solo un placeholder para Swagger UI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependencia para obtener el usuario actual y verificar si es admin
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    """
    Dependencia que verifica el token de Firebase ID y retorna los datos del usuario.
    Se usará en otras rutas protegidas.
    """
    try:
        user_data = await verify_id_token(token)
        return user_data
    except HTTPException as e:
        raise e # Re-lanza la excepción ya manejada por verify_id_token
    except Exception as e:
        log_event(None, 'AUTH_ERROR', {'detail': str(e), 'token_prefix': token[:10]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not validate credentials."
        )

async def get_current_admin_user(current_user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
    """
    Dependencia que verifica si el usuario actual es un administrador.
    """
    if not current_user.is_admin:
        log_event(current_user.uid, 'UNAUTHORIZED_ADMIN_ACCESS', {'email': current_user.email})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def api_register_user(user_data: UserRegister):
    """
    Registra un nuevo usuario en la aplicación.
    """
    return await register_user(user_data)

# @router.post("/login")
# async def api_login_user():
#     """
#     Endpoint para manejar el login. En esta arquitectura, el frontend
#     maneja el login directamente con Firebase y envía el ID Token.
#     Este endpoint no se usará para iniciar sesión con credenciales,
#     sino para verificar tokens si fuera necesario un flujo de sesión.
#     """
#     raise HTTPException(
#         status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
#         detail="Please use Firebase client SDK for login and send ID Token to protected routes."
#     )

@router.get("/debug-token")
async def debug_token(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """
    Debug route to show token information. For development only.
    """
    return {
        "uid": current_user.uid,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "message": "Token verification successful"
    }

# Ruta de prueba para verificar autenticación y rol
@router.get("/me", response_model=TokenData)
async def read_users_me(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """
    Obtiene información del usuario autenticado actualmente.
    Requiere un token de autenticación.
    """
    log_event(current_user.uid, 'FETCH_USER_INFO', {'email': current_user.email})
    return current_user

@router.get("/admin-only-test")
async def admin_only_route(current_admin_user: Annotated[TokenData, Depends(get_current_admin_user)]):
    """
    Ruta de prueba que solo es accesible por usuarios administradores.
    """
    log_event(current_admin_user.uid, 'ACCESS_ADMIN_ROUTE', {'email': current_admin_user.email})
    return {"message": f"Welcome, Admin {current_admin_user.email}! You have access to admin content."}

# Nota: Los endpoints de logout son típicamente manejados en el frontend,
# donde se elimina el token de Firebase del lado del cliente.
# El backend no necesita un endpoint de logout si no maneja sesiones de servidor.