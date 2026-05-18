from datetime import datetime

from pydantic import BaseModel


class BrandResponse(BaseModel):
    id: str
    name: str
    vendor_id: str
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    minimum_margin: float | None = None
    target_margin: float | None = None
    created_at: datetime
    updated_at: datetime


class BrandCreate(BaseModel):
    name: str
    vendor_id: str
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    minimum_margin: float | None = None
    target_margin: float | None = None


class BrandUpdate(BaseModel):
    name: str | None = None
    vendor_id: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    minimum_margin: float | None = None
    target_margin: float | None = None


class BrandFamilyProductResponse(BaseModel):
    id: str
    sku: str
    name: str | None = None
    price: float | None = None
    brand_id: str | None = None


class BrandFamilyResponse(BaseModel):
    id: str
    name: str | None = None
    code: str | None = None
    type: str | None = None
    brand_id: str
    product_code: str | None = None
    quantity: float | None = None
    discount: float | None = None
    minimum_margin: float | None = None
    target_margin: float | None = None
    unit: str | None = None
    packing: str | None = None
    lead_time_week: int | None = None
    net_price: float | None = None
    product_family_count: int = 0
    product: BrandFamilyProductResponse | None = None
