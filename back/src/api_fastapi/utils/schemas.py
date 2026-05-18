"""Pydantic schemas for utility routes."""

from pydantic import BaseModel, ConfigDict, Field


class FetchQuery(BaseModel):
    url: str | None = None
    max_chars: int = 10000
    timeout_ms: int = 8000


class FsCreateRequest(BaseModel):
    path: str | None = None
    type: str = "dir"


class FsReadRequest(BaseModel):
    path: str | None = None
    max_chars: int = 10000


class CurlRequest(BaseModel):
    url: str | None = None
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    max_chars: int = 10000
    timeout_ms: int = 8000


class GenericUtilityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
