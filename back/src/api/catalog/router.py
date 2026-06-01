from typing import List

from fastapi import APIRouter, Depends

from src.api.dependencies import get_database_repository
from src.repository.repository import DatabaseRepository
from .schemas import CatalogBrandResponse, CatalogFamilyListResponse, CatalogFamilyResponse

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



from fastapi import Query

@router.get("/api/catalog/families", response_model=List[CatalogFamilyResponse] | CatalogFamilyListResponse)
def list_catalog_families(
    db: DatabaseRepository = Depends(get_database_repository),
    brand_id: str = Query(None, description="Filtrer par marque (brand_id)"),
    limit: int | None = Query(
        None,
        ge=1,
        le=500,
        description="Nombre maximum de familles à retourner (None = pas de limite)",
    ),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    with_total: bool = Query(False, description="Inclure le total filtré dans la réponse"),
):
    where_clauses = []
    params = []
    count_params = []
    if brand_id:
        where_clauses.append("f.brand_id = %s")
        params.append(brand_id)
        count_params.append(brand_id)
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    pagination_sql = ""
    if limit is not None:
        pagination_sql = "LIMIT %s OFFSET %s"
        params.extend([limit, offset])

    query = f"""
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
               COALESCE(pfc.product_family_count, 0)::int AS product_family_count,
               p.id AS product_id,
               p.sku AS product_sku,
               p.name AS product_name,
               p.price AS product_price,
               p.brand_id AS product_brand_id
        FROM family f
        LEFT JOIN (
            SELECT family_id, COUNT(product_id) AS product_family_count
            FROM product_family
            GROUP BY family_id
        ) pfc ON pfc.family_id = f.id
        LEFT JOIN product p ON p.sku = f.product_code
        {where_sql}
        ORDER BY f.name ASC
        {pagination_sql}
    """

    rows = db.execute_dict_query(query, tuple(params))
    items = [
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

    if with_total:
        count_query = f"""
            SELECT COUNT(*) AS total
            FROM family f
            {where_sql}
        """
        count_rows = db.execute_dict_query(count_query, tuple(count_params))
        total = int((count_rows[0] or {}).get("total", 0)) if count_rows else 0
        return {"items": items, "total": total}

    return items
