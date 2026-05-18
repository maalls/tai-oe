"""FastAPI opportunity router for DDD opportunity endpoints."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_service_factory
from src.api_fastapi.opportunity.schemas import OpportunityAdvanceQuery, OpportunityAdvanceRequest, OpportunityQuery
from src.domain.enums import OpportunityStage
from src.infrastructure.factory import ServiceFactory

router = APIRouter(tags=["opportunity"])


def _serialize_opportunity(opportunity) -> dict:
    return jsonable_encoder(asdict(opportunity))


@router.get("/api/ddd/opportunity")
def get_opportunity(
    query: OpportunityQuery = Depends(),
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    if not query.opportunity_id:
        return JSONResponse({"status": "error", "message": "Missing opportunity_id"}, status_code=400)

    try:
        service = service_factory.create_opportunity_service()
        opportunity = service.get_opportunity(query.opportunity_id)
        return JSONResponse({"status": "ok", "opportunity": _serialize_opportunity(opportunity)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)


@router.get("/api/ddd/opportunity/advance")
def advance_opportunity_get(
    query: OpportunityAdvanceQuery = Depends(),
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    if not query.opportunity_id:
        return JSONResponse({"status": "error", "message": "Missing opportunity_id"}, status_code=400)
    if not query.stage:
        return JSONResponse({"status": "error", "message": "Missing stage"}, status_code=400)

    try:
        service = service_factory.create_opportunity_service()
        opportunity = service.advance_opportunity(query.opportunity_id, OpportunityStage(query.stage))
        return JSONResponse({"status": "ok", "opportunity": _serialize_opportunity(opportunity)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)


@router.post("/api/ddd/opportunity/advance")
def advance_opportunity_post(
    payload: OpportunityAdvanceRequest,
    service_factory: ServiceFactory = Depends(get_service_factory),
):
    try:
        service = service_factory.create_opportunity_service()
        opportunity = service.advance_opportunity(payload.opportunity_id, OpportunityStage(payload.stage))
        return JSONResponse({"status": "ok", "opportunity": _serialize_opportunity(opportunity)}, status_code=200)
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
