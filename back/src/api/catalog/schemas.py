from datetime import datetime

from pydantic import BaseModel


class CatalogBrandResponse(BaseModel):
    id: str
    name: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: datetime | None = None


class CatalogFamilyResponse(BaseModel):
    id: str
    name: str | None = None
    type: str | None = None
    brand_id: str
