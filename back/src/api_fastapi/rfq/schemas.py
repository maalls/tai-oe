"""Pydantic schemas for FastAPI RFQ endpoints."""

from pydantic import BaseModel, ConfigDict


class RfqGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = None
    content: str | None = None
    message_id: str | None = None
