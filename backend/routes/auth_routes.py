"""
Rutas de Autenticación - Endpoints de Gestión de Usuarios

Este módulo define todas las rutas relacionadas con la autenticación y autorización
de usuarios utilizando Firebase Authentication. Incluye funcionalidades para:

- Registro de nuevos usuarios
- Verificación de tokens JWT
- Gestión de roles y permisos
- Endpoints protegidos para administradores
- Logs de auditoría para eventos de seguridad

Seguridad implementada:
- Verificación de tokens JWT con Firebase
- Validación de custom claims para roles de administrador  
- Logging automático de eventos de seguridad
- Manejo robusto de errores de autenticación

Dependencias:
- Firebase Authentication para verificación de tokens
- OAuth2PasswordBearer para el esquema de autenticación
- Servicio de auditoría para tracking de eventos


"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from pydantic import BaseModel

# Importaciones de servicios locales
from services.auth_service import (
    register_user,
    verify_id_token,
    UserRegister,
    TokenData,
)
from utils.audit_logger import log_event

# ==================================================================================
#                           CONFIGURACIÓN DEL ROUTER
# ==================================================================================

# Router principal para todas las rutas de autenticación
router = APIRouter()

# Esquema OAuth2 para la documentación automática de Swagger
# tokenUrl debe coincidir con el endpoint real de login (si existe)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",  # URL relativa del endpoint de login
    description="Token JWT de Firebase Authentication"
)


# ==================================================================================
#                           DEPENDENCIAS DE AUTENTICACIÓN
# ==================================================================================

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    
    Esta función se ejecuta automáticamente en endpoints protegidos para:
    1. Extraer el token JWT del header Authorization
    2. Verificar la validez del token con Firebase
    3. Decodificar la información del usuario
    4. Validar que el token no haya expirado
    
    Args:
        token: Token JWT extraído del header "Authorization: Bearer <token>"
        
    Returns:
        TokenData: Información del usuario autenticado incluyendo UID, email y roles
        
    Raises:
        HTTPException 401: Si el token es inválido, expirado o malformado
        HTTPException 500: Si hay errores inesperados en la verificación
        
    Example:
        @router.get("/protected")
        async def protected_endpoint(user: TokenData = Depends(get_current_user)):
            return f"Hola {user.email}"
    """
    try:
        # Verificar y decodificar el token con Firebase Auth
        user_data = await verify_id_token(token)
        
        # Mensaje de depuración - comentado para producción
        # print(f"🔐 Usuario autenticado: {user_data.email}")
        
        return user_data
        
    except HTTPException:
        # Re-lanzar HTTPException sin modificar (ya tiene el código de estado correcto)
        raise
    except Exception as e:
        # Registrar error de autenticación para análisis de seguridad
        # Solo se registra el prefijo del token para evitar exposición de datos sensibles
        log_event(None, "AUTH_ERROR", {
            "detail": str(e),
            "token_prefix": token[:10] if len(token) > 10 else "invalid",
            "error_type": type(e).__name__
        })
        
        # Devolver error genérico para no exponer detalles internos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno de autenticación. Por favor, intenta de nuevo.",
        )


async def get_current_admin_user(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> TokenData:
    """
    Dependencia para verificar que el usuario actual tiene privilegios de administrador.
    
    Esta dependencia se utiliza en endpoints que requieren permisos de administrador.
    Verifica que el usuario esté autenticado Y tenga el custom claim 'admin' = True.
    
    Args:
        current_user: Usuario autenticado obtenido de get_current_user
        
    Returns:
        TokenData: Información del usuario administrador
        
    Raises:
        HTTPException 403: Si el usuario no tiene privilegios de administrador
        
    Example:
        @router.get("/admin-only")
        async def admin_endpoint(admin: TokenData = Depends(get_current_admin_user)):
            return "Solo administradores pueden ver esto"
    """
    # Verificar que el usuario tiene el custom claim de administrador
    if not current_user.is_admin:
        # Registrar intento de acceso no autorizado para auditoría de seguridad
        log_event(
            current_user.uid,
            "UNAUTHORIZED_ADMIN_ACCESS",
            {
                "email": current_user.email,
                "attempted_action": "admin_access",
                "timestamp": "2024-06-05T22:00:00Z"  # En producción, usar timestamp real
            },
        )
        
        # Devolver error 403 Forbidden
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador para acceder a este recurso.",
        )
    
    # Registrar acceso exitoso de administrador
    # Mensaje de depuración - comentado para producción
    # log_event(current_user.uid, "ADMIN_ACCESS_GRANTED", {"email": current_user.email})
    
    return current_user


# ==================================================================================
#                           ENDPOINTS DE AUTENTICACIÓN
# ==================================================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario en Firebase Authentication",
    response_description="Información del usuario creado",
    tags=["👤 Gestión de Usuarios"]
)
async def api_register_user(user: UserRegister):
    """
    Endpoint para registrar un nuevo usuario en el sistema.
    
    Este endpoint:
    1. Valida los datos de entrada (email, contraseña)
    2. Crea el usuario en Firebase Authentication
    3. Registra el evento en los logs de auditoría
    4. Devuelve la información del usuario creado
    
    Args:
        user: Datos del usuario a registrar (email, contraseña, nombre opcional)
        
    Returns:
        dict: Información del usuario registrado incluyendo UID
        
    Raises:
        HTTPException 400: Si los datos son inválidos
        HTTPException 409: Si el email ya está registrado
        HTTPException 500: Si hay errores durante el registro
        
    Example:
        POST /auth/register
        {
            "email": "usuario@ejemplo.com",
            "password": "contraseña_segura",
            "display_name": "Nombre Usuario"
        }
    """
    return await register_user(user)


@router.get(
    "/me",
    response_model=TokenData,
    summary="Obtener información del usuario actual",
    description="Devuelve la información del usuario autenticado",
    response_description="Datos del usuario actual",
    tags=["👤 Gestión de Usuarios"]
)
async def read_users_me(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Endpoint para obtener información del usuario actualmente autenticado.
    
    Este endpoint:
    1. Verifica que el usuario esté autenticado (mediante dependencia)
    2. Registra el acceso en los logs de auditoría
    3. Devuelve toda la información del usuario
    
    Args:
        current_user: Usuario autenticado (inyectado automáticamente)
        
    Returns:
        TokenData: Información completa del usuario (UID, email, roles, etc.)
        
    Example:
        GET /auth/me
        Headers: Authorization: Bearer <jwt_token>
        
        Response:
        {
            "uid": "user123",
            "email": "usuario@ejemplo.com",
            "is_admin": false,
            "email_verified": true
        }
    """
    # Registrar acceso a información de usuario para auditoría
    log_event(
        current_user.uid, 
        "FETCH_USER_INFO", 
        {
            "email": current_user.email,
            "endpoint": "/auth/me"
        }
    )
    
    return current_user


@router.get(
    "/admin-only-test",
    summary="Endpoint de prueba para administradores",
    description="Endpoint protegido que solo pueden acceder los administradores",
    response_description="Mensaje de bienvenida para administradores",
    tags=["🔐 Solo Administradores"]
)
async def admin_only_route(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)]
):
    """
    Endpoint de prueba para verificar permisos de administrador.
    
    Este endpoint está protegido y solo pueden acceder usuarios con custom claim 'admin' = True.
    Útil para probar la funcionalidad de roles y permisos.
    
    Args:
        current_admin: Usuario administrador (inyectado automáticamente)
        
    Returns:
        dict: Mensaje de bienvenida personalizado para el administrador
        
    Example:
        GET /auth/admin-only-test
        Headers: Authorization: Bearer <admin_jwt_token>
        
        Response:
        {
            "message": "¡Bienvenido, Admin admin@ejemplo.com!",
            "admin_privileges": true,
            "access_granted": true
        }
    """
    # Registrar acceso exitoso a endpoint de administrador
    log_event(
        current_admin.uid, 
        "ACCESS_ADMIN_ROUTE", 
        {
            "email": current_admin.email,
            "endpoint": "/auth/admin-only-test",
            "admin_verified": True
        }
    )
    
    return {
        "message": f"¡Bienvenido, Admin {current_admin.email}!",
        "admin_privileges": True,
        "access_granted": True,
        "timestamp": "2024-06-05T22:00:00Z"  # En producción, usar timestamp real
    }
