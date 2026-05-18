"""FastAPI product router for product CRUD endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_product_service
from src.api_fastapi.product.schemas import ProductUpsertRequest
from src.service.product.service import ProductService

router = APIRouter(tags=["product"])


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
