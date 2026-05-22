from typing import List

from fastapi import APIRouter, Depends

from src.api.dependencies import get_database_repository
from src.repository.database.repository import DatabaseRepository
from .schemas import CatalogBrandResponse, CatalogFamilyResponse

router = APIRouter()


@router.get("/api/catalog/brands", response_model=List[CatalogBrandResponse])
def list_catalog_brands(db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vendor_id, website, email, phone,
               minimum_margin, target_margin, created_at
        FROM brand
        ORDER BY name ASC
        """
    )
    return rows


@router.get("/api/catalog/families", response_model=List[CatalogFamilyResponse])
def list_catalog_families(db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT f.id,
               f.name,
               f.code,
               f.type,
               f.brand_id,
               f.product_code,
               f.quantity,
               f.discount,
               f.minimum_margin,
               f.target_margin,
               f.unit,
               f.packing,
               f.lead_time_week,
               f.net_price,
               COALESCE(COUNT(pf.product_id), 0)::int AS product_family_count,
               p.id AS product_id,
               p.sku AS product_sku,
               p.name AS product_name,
               p.price AS product_price,
               p.brand_id AS product_brand_id
        FROM family f
        LEFT JOIN product_family pf ON pf.family_id = f.id
        LEFT JOIN product p ON p.sku = f.product_code
        GROUP BY f.id, p.id, p.sku, p.name, p.price, p.brand_id
        ORDER BY name ASC
        """
    )
    return [
        {
            "id": row.get("id"),
            "name": row.get("name"),
            "code": row.get("code"),
            "type": row.get("type"),
            "brand_id": row.get("brand_id"),
            "product_code": row.get("product_code"),
            "quantity": row.get("quantity"),
            "discount": row.get("discount"),
            "minimum_margin": row.get("minimum_margin"),
            "target_margin": row.get("target_margin"),
            "unit": row.get("unit"),
            "packing": row.get("packing"),
            "lead_time_week": row.get("lead_time_week"),
            "net_price": row.get("net_price"),
            "product_family_count": row.get("product_family_count", 0),
            "product": {
                "id": row.get("product_id"),
                "sku": row.get("product_sku"),
                "name": row.get("product_name"),
                "price": row.get("product_price"),
                "brand_id": row.get("product_brand_id"),
            }
            if row.get("product_id") and row.get("product_sku")
            else None,
        }
        for row in rows
    ]
