"""Pydantic schemas for FastAPI quote endpoints."""

from pydantic import BaseModel, ConfigDict


class QuoteUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")


class QuoteDownloadQuery(BaseModel):
    inline: int = 0


class QuoteSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="allow")


class QuoteSendRequest(BaseModel):
    pdf_filename: str
    email: str
    body: str = "Hi, here is the quote"
