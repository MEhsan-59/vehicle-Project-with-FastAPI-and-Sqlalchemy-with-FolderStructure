from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_current_user, get_vehicle_service
from schemas import CarCreateRequest, CarKmUpdateRequest, MessageResponse
from services.vehicle_service import VehicleService

router = APIRouter()


def _raise_car_error(message: str) -> None:
    if message == "Car already exists.":
        status_code = 409
    elif message == "Car not found.":
        status_code = 404
    else:
        status_code = 400
    raise HTTPException(status_code=status_code, detail=message)


@router.post("", response_model=MessageResponse, status_code=201)
def add_car(
    payload: CarCreateRequest,
    current_user=Depends(get_current_user),
    service: VehicleService = Depends(get_vehicle_service),
) -> MessageResponse:
    success, message = service.add_car(
        payload.car_no,
        payload.model,
        payload.company,
        payload.onground_km,
        current_user.user_id,
    )
    if not success:
        _raise_car_error(message)
    return MessageResponse(status=True, message=message)


@router.delete("/{car_no}", response_model=MessageResponse)
def delete_car(
    car_no: str,
    current_user=Depends(get_current_user),
    service: VehicleService = Depends(get_vehicle_service),
) -> MessageResponse:
    success, message = service.delete_car(car_no.strip().upper(), current_user.user_id)
    if not success:
        _raise_car_error(message)
    return MessageResponse(status=True, message=message)


@router.put("/{car_no}/km", response_model=MessageResponse)
def update_car_km(
    car_no: str,
    payload: CarKmUpdateRequest,
    current_user=Depends(get_current_user),
    service: VehicleService = Depends(get_vehicle_service),
) -> MessageResponse:
    success, message = service.update_km(
        car_no.strip().upper(),
        payload.onground_km,
        current_user.user_id,
    )
    if not success:
        _raise_car_error(message)
    return MessageResponse(status=True, message=message)
