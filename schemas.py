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
