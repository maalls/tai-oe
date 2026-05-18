"""FastAPI product router for product CRUD endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api.dependencies import get_product_service
from src.api.product.schemas import ProductUpsertRequest
from src.repository.database.repository import DatabaseRepository
from src.service.product.service import ProductService

router = APIRouter(tags=["product"])


def get_db():
    return DatabaseRepository()


def _status_from_result(result: dict[str, Any], default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


def _to_front_product(product: dict[str, Any]) -> dict[str, Any]:
    brand = product.get("brand") or {}
    family_links = product.get("product_family") or []
    family_codes = []
    for link in family_links:
        family = (link or {}).get("family") or {}
        code = family.get("code")
        if code:
            family_codes.append(code)

    return {
        "id": product.get("id"),
        "marque": brand.get("name") or brand.get("marque") or "",
        "refciale": product.get("sku") or "",
        "libelle240": product.get("name") or "",
        "tarif": product.get("price") or 0,
        "family_codes": family_codes,
        "vector_text": product.get("vector_text") or "",
    }


@router.get("/api/products")
def products_list(
    sku: str | None = Query(default=None),
    limit: int = Query(default=10),
    product_service: ProductService = Depends(get_product_service),
):
    qs = {"sku": [sku], "limit": [str(limit)]}
    products = product_service.list_products(qs)
    return JSONResponse({"products": products}, status_code=200)


@router.get("/api/products/search")
def products_search(
    query: str | None = Query(default=None),
    marque: str | None = Query(default=None),
    refciale: str | None = Query(default=None),
    tarif: str | None = Query(default=None),
    family: str | None = Query(default=None),
    exact_match: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: DatabaseRepository = Depends(get_db),
):
    filters: list[str] = []
    params: list[Any] = []

    if query:
        token = f"%{query.strip()}%"
        filters.append(
            "(COALESCE(p.name, '') ILIKE %s OR COALESCE(p.sku, '') ILIKE %s OR COALESCE(b.name, '') ILIKE %s OR COALESCE(b.marque, '') ILIKE %s)"
        )
        params.extend([token, token, token, token])

    if marque:
        token = f"%{marque.strip()}%"
        filters.append("(COALESCE(b.name, '') ILIKE %s OR COALESCE(b.marque, '') ILIKE %s)")
        params.extend([token, token])

    if refciale:
        filters.append("COALESCE(p.sku, '') ILIKE %s")
        params.append(refciale.strip() if exact_match else f"%{refciale.strip()}%")

    if tarif:
        filters.append("COALESCE(p.price::text, '') ILIKE %s")
        params.append(f"%{tarif.strip()}%")

    if family:
        filters.append(
            "EXISTS (SELECT 1 FROM product_family pf2 JOIN family f2 ON f2.id = pf2.family_id WHERE pf2.product_id = p.id AND LOWER(COALESCE(f2.code, '')) = LOWER(%s))"
        )
        params.append(family.strip())

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute_dict_query(
        f"""
        WITH filtered_products AS (
            SELECT p.id,
                   COALESCE(b.marque, b.name, '') AS marque,
                   COALESCE(p.sku, '') AS refciale,
                   COALESCE(p.name, '') AS libelle240,
                   COALESCE(p.price, 0) AS tarif,
                   p.brand_id,
                   b.name AS brand_name,
                   COALESCE(array_remove(array_agg(DISTINCT f.code), NULL), ARRAY[]::text[]) AS family_codes
            FROM product p
            LEFT JOIN brand b ON b.id = p.brand_id
            LEFT JOIN product_family pf ON pf.product_id = p.id
            LEFT JOIN family f ON f.id = pf.family_id
            {where_clause}
            GROUP BY p.id, b.id, b.name, b.marque
        )
        SELECT id,
               marque,
               refciale,
               libelle240,
               tarif,
               brand_id,
               brand_name,
               family_codes,
               COUNT(*) OVER() AS total_count
        FROM filtered_products
        ORDER BY refciale ASC
        LIMIT %s OFFSET %s
        """,
        tuple([*params, limit, offset]),
    )

    total_count = rows[0]["total_count"] if rows else 0
    return JSONResponse(
        {
            "products": [
                {
                    "id": row["id"],
                    "marque": row["marque"],
                    "refciale": row["refciale"],
                    "libelle240": row["libelle240"],
                    "tarif": row["tarif"],
                    "brand_id": row.get("brand_id"),
                    "brand_name": row.get("brand_name"),
                    "family_codes": row.get("family_codes") or [],
                }
                for row in rows
            ],
            "total_count": total_count,
        },
        status_code=200,
    )


@router.post("/api/products")
def products_create(
    payload: ProductUpsertRequest,
    product_service: ProductService = Depends(get_product_service),
):
    try:
        product = product_service.post_product(payload.model_dump())
        return JSONResponse({"status": "ok", "product": product}, status_code=201)
    except Exception as exc:
        result = {"status": "error", "message": str(exc)}
        return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/products/{product_id}")
def product_get(
    product_id: str,
    product_service: ProductService = Depends(get_product_service),
):
    try:
        product = product_service.get_product_by_id(product_id)
        if not product:
            return JSONResponse({"status": "error", "message": "Product not found"}, status_code=404)
        return JSONResponse(_to_front_product(product), status_code=200)
    except Exception as exc:
        result = {"status": "error", "message": str(exc)}
        return JSONResponse(result, status_code=_status_from_result(result))


@router.put("/api/products/{product_id}")
def product_update(
    product_id: str,
    payload: ProductUpsertRequest,
    product_service: ProductService = Depends(get_product_service),
):
    try:
        product = product_service.update_product(product_id=product_id, payload=payload.model_dump())
        return JSONResponse({"status": "ok", "product": product}, status_code=200)
    except Exception as exc:
        result = {"status": "error", "message": str(exc)}
        return JSONResponse(result, status_code=_status_from_result(result))
