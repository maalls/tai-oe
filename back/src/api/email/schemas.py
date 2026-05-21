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


class ProviderStatusQuery(BaseModel):
    user_id: str | None = None


class ProviderOauthStartQuery(BaseModel):
    redirect_url: str | None = None
    user_id: str | None = None


class ProviderUserQuery(BaseModel):
    user_id: str | None = None


class ProviderMessagesQuery(BaseModel):
    user_id: str | None = None
    max_results: int = 20
    force: bool = False


class ProviderOauthCallbackQuery(BaseModel):
    code: str
    state: str | None = None


class ImapConfigRequest(BaseModel):
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    mailbox: str | None = None
    use_ssl: bool = True
    enabled: bool = True


class EmailResyncRequest(BaseModel):
    provider_message_id: str


class GenericEmailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str | None = None
    message: str | None = None
