from pydantic import BaseModel, Field


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
