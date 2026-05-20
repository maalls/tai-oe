"""Pydantic schemas for product FastAPI routes."""

from pydantic import BaseModel, Field, field_validator


class ProductUpsertRequest(BaseModel):
    brand_id: str | None = None
    marque: str
    refciale: str
    libelle240: str
    tarif: float
    batch: int = Field(default=1, ge=1)
    family_codes: list[str] | str
    vector_text: str = ""

    @field_validator("family_codes", mode="before")
    @classmethod
    def _normalize_family_codes(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return value
