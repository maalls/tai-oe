"""FastAPI product router for product CRUD endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
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
    brand_id = product.get("brand_id") or brand.get("id")
    brand_name = brand.get("name") or brand.get("marque") or ""
    family_links = product.get("product_family") or []
    media_rows = product.get("product_media") or []
    family_codes = []
    for link in family_links:
        family = (link or {}).get("family") or {}
        code = family.get("code")
        if code:
            family_codes.append(code)

    media = sorted(
        [row for row in media_rows if isinstance(row, dict) and row.get("url")],
        key=lambda row: (
            row.get("position") is None,
            row.get("position") or 0,
            str(row.get("created_at") or ""),
        ),
    )

    return {
        "id": product.get("id"),
        "marque": brand.get("name") or brand.get("marque") or "",
        "brand_id": brand_id,
        "brand_name": brand_name,
        "refciale": product.get("sku") or "",
        "libelle240": product.get("name") or "",
        "tarif": product.get("price") or 0,
        "batch": product.get("batch"),
        "family_codes": family_codes,
        "media": [
            {
                "id": row.get("id"),
                "url": row.get("url"),
                "type": row.get("type"),
                "source": row.get("source"),
                "position": row.get("position"),
                "created_at": row.get("created_at"),
            }
            for row in media
        ],
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
    normalized_products = []
    for product in products:
        if isinstance(product, dict):
            normalized_products.append({**product, "brand": product.get("brand") or {}})
        else:
            normalized_products.append(product)
    return JSONResponse({"products": normalized_products}, status_code=200)


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
                 p.batch,
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
             batch,
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
    payload = {
        "products": [
            {
                "id": row["id"],
                "marque": row["marque"],
                "refciale": row["refciale"],
                "libelle240": row["libelle240"],
                "tarif": row["tarif"],
                "batch": row.get("batch"),
                "brand_id": row.get("brand_id"),
                "brand_name": row.get("brand_name"),
                "family_codes": row.get("family_codes") or [],
            }
            for row in rows
        ],
        "total_count": total_count,
    }
    return JSONResponse(jsonable_encoder(payload), status_code=200)


@router.get("/api/products/quote-context")
def products_quote_context(
    sku: list[str] = Query(default=[]),
    db: DatabaseRepository = Depends(get_db),
):
    skus = [value.strip() for value in sku if value and value.strip()]
    if not skus:
        return JSONResponse({"products": [], "net_price_families": []}, status_code=200)

    placeholders = ", ".join(["%s"] * len(skus))
    product_rows = db.execute_dict_query(
        f"""
        SELECT p.id,
               p.sku,
               p.name,
               p.price,
               p.batch,
               p.brand_id,
               b.id AS brand_ref_id,
               b.name AS brand_name,
               b.marque AS brand_marque,
               b.minimum_margin AS brand_minimum_margin,
               b.target_margin AS brand_target_margin,
               f.id AS family_id,
               f.name AS family_name,
               f.code AS family_code,
               f.type AS family_type,
               f.discount AS family_discount,
               f.minimum_margin AS family_minimum_margin,
               f.target_margin AS family_target_margin,
               f.quantity AS family_quantity,
               f.net_price AS family_net_price,
               f.product_code AS family_product_code
        FROM product p
        LEFT JOIN brand b ON b.id = p.brand_id
        LEFT JOIN product_family pf ON pf.product_id = p.id
        LEFT JOIN family f ON f.id = pf.family_id
        WHERE p.sku IN ({placeholders})
        ORDER BY p.sku ASC
        """,
        tuple(skus),
    )
    net_price_rows = db.execute_dict_query(
        f"""
        SELECT id,
               name,
               code,
               type,
               product_code,
               quantity,
               discount,
               minimum_margin,
               target_margin,
               net_price
        FROM family
        WHERE LOWER(type) = 'net_price'
          AND product_code IN ({placeholders})
        ORDER BY product_code ASC
        """,
        tuple(skus),
    )

    products_by_sku: dict[str, dict[str, Any]] = {}
    for row in product_rows:
        product_sku = row.get("sku")
        if not product_sku:
            continue

        product = products_by_sku.setdefault(
            product_sku,
            {
                "id": row.get("id"),
                "sku": product_sku,
                "name": row.get("name"),
                "price": row.get("price"),
                "batch": row.get("batch"),
                "brand_id": row.get("brand_id"),
                "brand": {
                    "id": row.get("brand_ref_id"),
                    "name": row.get("brand_name"),
                    "marque": row.get("brand_marque"),
                    "minimum_margin": row.get("brand_minimum_margin"),
                    "target_margin": row.get("brand_target_margin"),
                },
                "product_family": [],
            },
        )

        if row.get("family_id"):
            product["product_family"].append(
                {
                    "family": {
                        "id": row.get("family_id"),
                        "name": row.get("family_name"),
                        "code": row.get("family_code"),
                        "type": row.get("family_type"),
                        "discount": row.get("family_discount"),
                        "minimum_margin": row.get("family_minimum_margin"),
                        "target_margin": row.get("family_target_margin"),
                        "quantity": row.get("family_quantity"),
                        "net_price": row.get("family_net_price"),
                        "product_code": row.get("family_product_code"),
                    }
                }
            )

    payload = {
        "products": list(products_by_sku.values()),
        "net_price_families": net_price_rows,
    }

    # Some DB drivers return Decimal for numeric columns; encode before JSONResponse.
    return JSONResponse(jsonable_encoder(payload), status_code=200)


@router.post("/api/products")
def products_create(
    payload: ProductUpsertRequest,
    product_service: ProductService = Depends(get_product_service),
):
    try:
        product = product_service.post_product(payload.model_dump())
        return JSONResponse({"status": "ok", "product": product}, status_code=201)
    except ValueError as exc:
        result = {"status": "error", "message": str(exc)}
        return JSONResponse(result, status_code=400)
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


@router.delete("/api/products/{product_id}")
def product_delete(
    product_id: str,
    db: DatabaseRepository = Depends(get_db),
):
    rows = db.execute_dict_query(
        "DELETE FROM product_family WHERE product_id = %s",
        (product_id,),
    )
    _ = rows
    rows = db.execute_dict_query(
        "DELETE FROM product WHERE id = %s RETURNING id",
        (product_id,),
    )
    if not rows:
        return JSONResponse({"status": "error", "message": "Product not found"}, status_code=404)
    return JSONResponse({"status": "ok", "id": rows[0]["id"]}, status_code=200)
