# backend/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from pydantic import BaseModel
from services.auth_service import (
    register_user,
    verify_id_token,
    UserRegister,
    TokenData,
)
from utils.audit_logger import log_event

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---------------------------------------------------------------------------
# Dependencias comunes
# ---------------------------------------------------------------------------
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    try:
        return await verify_id_token(token)
    except HTTPException as e:
        raise e
    except Exception as e:
        log_event(None, "AUTH_ERROR", {"detail": str(e), "token_prefix": token[:10]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not validate credentials.",
        )

async def get_current_admin_user(
    current_user: Annotated[TokenData, Depends(get_current_user)]
) -> TokenData:
    if not current_user.is_admin:
        log_event(
            current_user.uid,
            "UNAUTHORIZED_ADMIN_ACCESS",
            {"email": current_user.email},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user

# ---------------------------------------------------------------------------
# Endpoints de autenticación
# ---------------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def api_register_user(user: UserRegister):
    return await register_user(user)

@router.get("/me", response_model=TokenData)
async def read_users_me(current_user: Annotated[TokenData, Depends(get_current_user)]):
    log_event(current_user.uid, "FETCH_USER_INFO", {"email": current_user.email})
    return current_user

@router.get("/admin-only-test")
async def admin_only_route(
    current_admin: Annotated[TokenData, Depends(get_current_admin_user)]
):
    log_event(
        current_admin.uid, "ACCESS_ADMIN_ROUTE", {"email": current_admin.email}
    )
    return {"message": f"Welcome, Admin {current_admin.email}!"}
