"""Pydantic schemas for FastAPI vendor endpoints."""

from pydantic import BaseModel


class VendorQuery(BaseModel):
    vendor_id: str | None = None
