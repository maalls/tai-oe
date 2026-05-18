"""Pydantic schemas for document FastAPI routes."""

from pydantic import BaseModel


class DocumentExtractRfpRequest(BaseModel):
    document_id: str


class DocumentUpdateContentRequest(BaseModel):
    document_id: str
    content: str
