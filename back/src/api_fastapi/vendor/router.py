"""FastAPI vendor router."""

from dataclasses import asdict
from dataclasses import is_dataclass

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_service_factory
from src.api_fastapi.vendor.schemas import VendorQuery
from src.infrastructure.factory import ServiceFactory

router = APIRouter(tags=["vendor"])


def _serialize_vendor(vendor) -> dict:
    if is_dataclass(vendor):
        return jsonable_encoder(asdict(vendor))
    if isinstance(vendor, dict):
        return jsonable_encoder(vendor)
    return jsonable_encoder(vars(vendor))


@router.get("/api/vendor")
def get_vendor(
    query: VendorQuery = Depends(),
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    if not query.vendor_id:
        return JSONResponse({"status": "error", "message": "Missing vendor_id"}, status_code=400)

    try:
        service = service_factory.create_vendor_service()
        vendor = service.get_vendor(query.vendor_id)
        return JSONResponse({"status": "ok", "vendor": _serialize_vendor(vendor)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
