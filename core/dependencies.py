from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth import decode_access_token, decode_settings_token
from core.database import get_db
from repositories.account_repository import AccountRepository
from repositories.part_repository import PartRepository
from services.account_service import AccountService
from services.part_service import PartService

security_scheme = HTTPBearer()


def get_account_service(db=Depends(get_db)):
    return AccountService(AccountRepository(db))


def get_part_service(db=Depends(get_db)):
    return PartService(PartRepository(db))


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    service: AccountService = Depends(get_account_service),
):
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    account = service.get_account_by_id(payload.get("sub"))
    if account is None:
        raise HTTPException(status_code=401, detail="User not found")
    return account


def require_settings_unlock(
    x_settings_token: str | None = Header(None, alias="X-Settings-Token"),
    current_user=Depends(get_current_user),
):
    payload = decode_settings_token(x_settings_token) if x_settings_token else None
    if payload is None or payload.get("sub") != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Settings locked. Enter your password at /settings/unlock first.",
        )
    return current_user
