from fastapi import APIRouter, Depends

from core.dependencies import get_current_user, get_expiry_service
from schemas import ExpiryResponse
from services.expiry_service import ExpiryService

router = APIRouter()


@router.get("", response_model=list[ExpiryResponse])
def get_expiry(
    current_user=Depends(get_current_user),
    service: ExpiryService = Depends(get_expiry_service),
) -> list[ExpiryResponse]:
    return service.get_all_expiry(current_user.user_id)
