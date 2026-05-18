"""Pydantic schemas for FastAPI vendor endpoints."""

from datetime import datetime

from pydantic import BaseModel


class VendorResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    created_at: datetime
    updated_at: datetime
    brand_count: int | None = None
    family_count: int | None = None
    product_count: int | None = None


class VendorCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    website: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
