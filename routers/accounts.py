from fastapi import APIRouter, Depends, HTTPException

from core.auth import create_settings_token
from core.config import settings
from core.dependencies import get_account_service, get_current_user
from schemas import (
    CreateAccountRequest,
    CreateAccountResponse,
    LoginRequest,
    ProfileResponse,
    SettingsUnlockRequest,
    SettingsUnlockResponse,
    TokenResponse,
)
from services.account_manager import AccountManager as AccountService

router = APIRouter()


@router.post("/create_account")
def create_account(
    payload: CreateAccountRequest,
    service: AccountService = Depends(get_account_service),
) -> CreateAccountResponse:
    result = service.create_account(payload.user_id, payload.user_name, payload.password)
    if not result["status"]:
        status_code = 409 if result["message"] == "Account already exists." else 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result


@router.post("/login_account", response_model=TokenResponse)
def login_account(
    payload: LoginRequest,
    service: AccountService = Depends(get_account_service),
):
    result = service.login_account(payload.user_id, payload.password)
    if not result["status"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@router.get("/me", response_model=ProfileResponse)
def get_profile(current_user=Depends(get_current_user)):
    return {
        "message": f"Welcome, {current_user.user_name}!",
        "user_id": current_user.user_id,
        "name": current_user.user_name,
    }


@router.post("/settings/unlock", response_model=SettingsUnlockResponse)
def unlock_settings(
    payload: SettingsUnlockRequest,
    current_user=Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
):
    if not service.verify_password(current_user.user_id, payload.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    return {
        "settings_token": create_settings_token(current_user.user_id),
        "expires_in_minutes": settings.SETTINGS_TOKEN_EXPIRE_MINUTES,
    }
