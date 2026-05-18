"""Pydantic schemas for product FastAPI routes."""

from pydantic import BaseModel


class ProductUpsertRequest(BaseModel):
    marque: str
    refciale: str
    libelle240: str
    tarif: float
    family_codes: list[str]
    vector_text: str = ""
