# indexador-demo/backend/services/auth_service.py

from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError
from services.firebase_service import get_auth_client, get_firestore_client
from utils.audit_logger import log_event
from fastapi import HTTPException, status
from pydantic import BaseModel


# ---------- MODELOS DE Pydantic ----------
class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    uid: str
    email: str
    is_admin: bool = False


# ---------- FUNCIÓN: Registrar Usuario ----------
async def register_user(user_data: UserRegister):
    """
    Registra un nuevo usuario en Firebase Authentication.
    """
    try:
        firebase_auth = get_auth_client()

        user = firebase_auth.create_user(
            email=user_data.email,
            password=user_data.password,
            email_verified=False,
            disabled=False
        )

        firestore_client = get_firestore_client()
        firestore_client.collection("users").document(user.uid).set({
            "email": user.email,
            "role": "user",
            "created_at": firestore.SERVER_TIMESTAMP
        })

        log_event(user.uid, 'USER_REGISTERED', {'email': user.email})

        return {"uid": user.uid, "email": user.email, "message": "User registered successfully."}

    except FirebaseError as e:
        if "EMAIL_ALREADY_EXISTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Firebase registration error: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during registration: {e}"
        )


# ---------- FUNCIÓN: Verificar Token ----------
async def verify_id_token(id_token: str) -> TokenData:
    """
    Verifica el token de Firebase enviado por el cliente y retorna los datos del usuario.
    """
    try:
        decoded_token = get_auth_client().verify_id_token(id_token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")
        
        # Check for admin claim in the token
        # Custom claims are at the root level of the decoded token
        is_admin = decoded_token.get("admin", False)

        return TokenData(uid=uid, email=email, is_admin=is_admin)

    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------- FUNCIÓN: Promover usuario a admin ----------
async def set_user_as_admin(uid: str):
    """
    Establece el custom claim 'admin' en un usuario.
    """
    try:
        firebase_auth = get_auth_client()

        firebase_auth.set_custom_user_claims(uid, {'admin': True})
        print(f"Custom claim 'admin: True' establecido para el usuario UID: {uid}")

        firestore_client = get_firestore_client()
        firestore_client.collection("users").document(uid).update({"role": "admin"})

        log_event(uid, 'USER_PROMOTED_TO_ADMIN', {})
    except FirebaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error setting admin claims: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while setting admin claims: {e}"
        )
