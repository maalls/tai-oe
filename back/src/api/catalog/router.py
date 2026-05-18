from typing import List

from fastapi import APIRouter, Depends

from src.repository.database.repository import DatabaseRepository
from .schemas import CatalogBrandResponse, CatalogFamilyResponse

router = APIRouter()


def get_db():
    return DatabaseRepository()


@router.get("/api/catalog/brands", response_model=List[CatalogBrandResponse])
def list_catalog_brands(db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, website, email, phone, created_at
        FROM brand
        ORDER BY name ASC
        """
    )
    return rows


@router.get("/api/catalog/families", response_model=List[CatalogFamilyResponse])
def list_catalog_families(db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, type, brand_id
        FROM family
        ORDER BY name ASC
        """
    )
    return rows
