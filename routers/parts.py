from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import (
    get_current_user,
    get_part_service,
    require_settings_unlock,
)
from schemas import (
    MessageResponse,
    PartConfigRequest,
    PartConfigResponse,
    PartUpdateRequest,
)
from services.part_manager import PartManager as PartService

router = APIRouter()


@router.post("", response_model=MessageResponse, status_code=201)
def add_part(
    payload: PartConfigRequest,
    current_user=Depends(require_settings_unlock),
    service: PartService = Depends(get_part_service),
) -> MessageResponse:
    result = service.add_part(
        current_user.user_id,
        payload.part,
        payload.km_life,
        payload.month_life,
        payload.km_limit,
        payload.day_limit,
    )
    if not result["status"]:
        status_code = 409 if result["message"] == "Part already exists." else 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result


@router.put("/{part}", response_model=MessageResponse)
def update_part(
    part: str,
    payload: PartUpdateRequest,
    current_user=Depends(require_settings_unlock),
    service: PartService = Depends(get_part_service),
) -> MessageResponse:
    result = service.update_part(
        current_user.user_id,
        part.strip().lower(),
        payload.km_life,
        payload.month_life,
        payload.km_limit,
        payload.day_limit,
    )
    if not result["status"]:
        if result["message"] == "Part not found.":
            status_code = 404
        elif result["message"].startswith("Part is in use"):
            status_code = 409
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result


@router.delete("/{part}", response_model=MessageResponse)
def delete_part(
    part: str,
    current_user=Depends(require_settings_unlock),
    service: PartService = Depends(get_part_service),
) -> MessageResponse:
    result = service.delete_part(current_user.user_id, part.strip().lower())
    if not result["status"]:
        if result["message"] == "Part not found.":
            status_code = 404
        elif result["message"].startswith("Part is in use"):
            status_code = 409
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result


@router.get("", response_model=list[PartConfigResponse])
def get_parts(
    current_user=Depends(get_current_user),
    service: PartService = Depends(get_part_service),
) -> list[PartConfigResponse]:
    return service.get_all_parts(current_user.user_id)
