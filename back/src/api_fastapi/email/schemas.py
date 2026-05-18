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


class GmailMessagesQuery(BaseModel):
    user_id: str | None = None
    max_results: int = 20
    force: bool = False


class GmailClassifyQuery(BaseModel):
    user_id: str | None = None
    limit: int = 200


class GmailOauthCallbackQuery(BaseModel):
    code: str
    state: str | None = None


class GenericEmailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str | None = None
    message: str | None = None
