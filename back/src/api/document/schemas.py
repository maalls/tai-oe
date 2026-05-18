"""Pydantic schemas for document FastAPI routes."""

from pydantic import BaseModel


class DocumentExtractRfpRequest(BaseModel):
    document_id: str


class DocumentUpdateContentRequest(BaseModel):
    document_id: str
    content: str


class DocumentUpdateStorageKeyRequest(BaseModel):
    storage_key: str | None = None


class DocumentUpdateStatusRequest(BaseModel):
    status: str
