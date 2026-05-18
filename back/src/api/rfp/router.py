"""FastAPI RFP router."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.dependencies import get_service_factory
from src.api.rfp.schemas import RfpQuery, RfpSubmitRequest
from src.infrastructure.factory import ServiceFactory

router = APIRouter(tags=["rfp"])


def _serialize_rfp(rfp) -> dict:
    return jsonable_encoder(asdict(rfp))


@router.get("/api/rfp")
def get_rfp(
    query: RfpQuery = Depends(),
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    if not query.rfp_id:
        return JSONResponse({"status": "error", "message": "Missing rfp_id"}, status_code=400)

    try:
        service = service_factory.create_rfp_service()
        rfp = service.get_rfp(query.rfp_id)
        return JSONResponse({"status": "ok", "rfp": _serialize_rfp(rfp)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)


@router.get("/api/rfp/submit")
def submit_rfp_get(
    query: RfpQuery = Depends(),
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    if not query.rfp_id:
        return JSONResponse({"status": "error", "message": "Missing rfp_id"}, status_code=400)

    try:
        service = service_factory.create_rfp_service()
        rfp = service.submit_rfp(query.rfp_id)
        return JSONResponse({"status": "ok", "rfp": _serialize_rfp(rfp)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)


@router.post("/api/rfp/submit")
def submit_rfp_post(
    payload: RfpSubmitRequest,
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    try:
        service = service_factory.create_rfp_service()
        rfp = service.submit_rfp(payload.rfp_id)
        return JSONResponse({"status": "ok", "rfp": _serialize_rfp(rfp)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
