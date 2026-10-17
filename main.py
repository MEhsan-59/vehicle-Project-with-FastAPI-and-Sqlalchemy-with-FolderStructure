from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.database import Base, engine, get_db
from core.auth import decode_access_token
from repositories.account_repository import AccountRepository
from schemas import (
    CreateAccountRequest,
    CreateAccountResponse,
    LoginRequest,
    ProfileResponse,
    TokenResponse,
)
from services.account_service import AccountService

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API")
security_scheme = HTTPBearer()


def get_account_service(db=Depends(get_db)):
    return AccountService(AccountRepository(db))


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


@app.post("/create_account")
def create_account(
    payload: CreateAccountRequest,
    service: AccountService = Depends(get_account_service),
) -> CreateAccountResponse:
    result = service.create_account(payload.user_id, payload.user_name, payload.password)
    if not result["status"]:
        status_code = 409 if result["message"] == "Account already exists." else 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result


@app.post("/login_account", response_model=TokenResponse)
def login_account(
    payload: LoginRequest,
    service: AccountService = Depends(get_account_service),
):
    result = service.login_account(payload.user_id, payload.password)
    if not result["status"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@app.get("/me", response_model=ProfileResponse)
def get_profile(current_user=Depends(get_current_user)):
    return {
        "message": f"Welcome, {current_user.user_name}!",
        "user_id": current_user.user_id,
        "name": current_user.user_name,
    }
