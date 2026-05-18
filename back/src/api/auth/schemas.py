"""Pydantic schemas for FastAPI auth endpoints."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email")
        return normalized


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email")
        return normalized


class OAuthLoginQuery(BaseModel):
    provider: str = Field(min_length=1)
    redirect_url: str | None = None


class OAuthCallbackQuery(BaseModel):
    provider: str = Field(min_length=1)
    code: str = Field(min_length=1)
    state: str | None = None


class AuthSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    user: dict[str, Any] | None = None
    session: dict[str, Any] | None = None
    access_token: str | None = None


class AuthUserResponse(BaseModel):
    user: dict[str, Any]


class AuthMessageResponse(BaseModel):
    message: str


class AuthErrorResponse(BaseModel):
    error: str
