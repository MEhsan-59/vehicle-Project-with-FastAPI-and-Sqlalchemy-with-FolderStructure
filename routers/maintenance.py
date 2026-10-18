from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user, get_maintenance_service
from schemas import (
    MaintenanceDetailResponse,
    MaintenanceUpdateRequest,
    MessageResponse,
)
from services.maintenance_service import MaintenanceService

router = APIRouter()


@router.get("/maintenance", response_model=list[MaintenanceDetailResponse])
def view_car_maintenance(
    filter_type: Literal["all", "car", "part"] = "all",
    value: str | None = Query(
        None,
        description="Car number or part name when filtering by car or part",
    ),
    current_user=Depends(get_current_user),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> list[MaintenanceDetailResponse]:
    if filter_type != "all" and (value is None or not value.strip()):
        raise HTTPException(
            status_code=400,
            detail="Value is required for car and part filters.",
        )
    return service.get_vehicle_details(
        current_user.user_id,
        filter_type,
        value,
    )


@router.put("/{car_no}/parts/{part}", response_model=MessageResponse)
def update_part_on_car(
    car_no: str,
    part: str,
    payload: MaintenanceUpdateRequest,
    current_user=Depends(get_current_user),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MessageResponse:
    success, message = service.update_part(
        car_no.strip().upper(),
        part.strip().lower(),
        payload.changed_km,
        payload.changed_date,
        current_user.user_id,
    )
    if not success:
        if message in ("Car not found.", "Part not found."):
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)
    return MessageResponse(status=True, message=message)
