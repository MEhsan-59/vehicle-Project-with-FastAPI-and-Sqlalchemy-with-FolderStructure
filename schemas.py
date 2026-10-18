from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateAccountRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=30)
    user_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class CreateAccountResponse(BaseModel):
    status: bool
    message: str


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ProfileResponse(BaseModel):
    message: str
    user_id: str
    name: str


class PartConfigRequest(BaseModel):
    part: str = Field(..., min_length=1, max_length=50)
    km_life: int = Field(..., gt=0)
    month_life: int = Field(..., gt=0)
    km_limit: int = Field(..., ge=0)
    day_limit: int = Field(..., ge=0)

    @field_validator("part")
    @classmethod
    def clean_part(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("Must not be empty")
        return value


class PartUpdateRequest(BaseModel):
    km_life: int = Field(..., gt=0)
    month_life: int = Field(..., gt=0)
    km_limit: int = Field(..., ge=0)
    day_limit: int = Field(..., ge=0)


class PartConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part: str
    km_life: int
    month_life: int
    km_limit: int
    day_limit: int
    is_default: bool


class MessageResponse(BaseModel):
    status: bool
    message: str


class SettingsUnlockRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=72)


class SettingsUnlockResponse(BaseModel):
    settings_token: str
    expires_in_minutes: int


class CarCreateRequest(BaseModel):
    car_no: str = Field(..., min_length=1, max_length=20)
    model: str = Field(..., min_length=1, max_length=50)
    company: str = Field(..., min_length=1, max_length=50)
    onground_km: int = Field(0, ge=0)

    @field_validator("car_no")
    @classmethod
    def clean_car_no(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Must not be empty")
        return value

    @field_validator("model", "company")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must not be empty")
        return value


class CarKmUpdateRequest(BaseModel):
    onground_km: int = Field(..., ge=0)


class MaintenanceUpdateRequest(BaseModel):
    changed_km: int = Field(..., ge=0)
    changed_date: date


class ExpiryResponse(BaseModel):
    car_no: str
    model: str
    company: str
    part: str
    status: Literal["expired", "expiring"]
    remaining_km: int
    remaining_days: int
    next_changed_km: int
    next_changed_date: date
    message: str


class MaintenanceDetailResponse(BaseModel):
    car_no: str
    model: str
    company: str
    onground_km: int
    part: str
    km_limit: int
    day_limit: int
    changed_km: int
    next_changed_km: int
    changed_date: date
    next_changed_date: date


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int | None
    car_no: str
    action_type: str
    part_name: str | None
    changed_km: int | None
    changed_date: date | None
    action_timestamp: datetime | None
    active_user: str
    details: str | None
