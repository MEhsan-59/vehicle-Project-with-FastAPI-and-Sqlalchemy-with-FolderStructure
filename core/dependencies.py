from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth import decode_access_token, decode_settings_token
from core.database import get_db
from repositories.account_repository import AccountRepository
from repositories.history_repository import HistoryRepository
from repositories.maintenance_repository import MaintenanceRepository
from repositories.part_repository import PartRepository
from repositories.vehicle_repository import VehicleRepository
from services.account_manager import AccountManager as AccountService
from services.expiry_service import ExpiryService
from services.history_service import HistoryService
from services.maintenance_service import MaintenanceService
from services.part_manager import PartManager as PartService
from services.vehicle_service import VehicleService

security_scheme = HTTPBearer()


def get_account_service(db=Depends(get_db)):
    return AccountService(AccountRepository(db))


def get_part_service(db=Depends(get_db)):
    return PartService(PartRepository(db))


def get_vehicle_service(db=Depends(get_db)):
    return VehicleService(VehicleRepository(db))


def get_history_service(db=Depends(get_db)):
    return HistoryService(HistoryRepository(db))


def get_maintenance_service(db=Depends(get_db)):
    return MaintenanceService(
        VehicleRepository(db),
        MaintenanceRepository(db),
        PartRepository(db),
    )


def get_expiry_service(
    service: MaintenanceService = Depends(get_maintenance_service),
):
    return ExpiryService(service)


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
