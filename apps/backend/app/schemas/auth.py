from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    created_at: datetime


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in_seconds: int
    refresh_expires_in_seconds: int
    user: AuthUserRead


class AuthRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


class AuthLogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)
