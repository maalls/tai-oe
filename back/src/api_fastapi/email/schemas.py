"""Pydantic schemas for FastAPI email endpoints."""

from pydantic import BaseModel, ConfigDict


class GmailStatusQuery(BaseModel):
    user_id: str | None = None


class GmailAuthorizeQuery(BaseModel):
    redirect_url: str | None = None


class GmailOauthStartQuery(BaseModel):
    redirect_url: str | None = None
    user_id: str | None = None


class GmailUserQuery(BaseModel):
    user_id: str | None = None


class GenericEmailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str | None = None
    message: str | None = None
