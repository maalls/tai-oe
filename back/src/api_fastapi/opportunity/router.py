"""FastAPI opportunity router."""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import (
    get_auth_service,
    get_email_repository,
    get_opportunity_repository,
    get_quote_send_service,
    get_rfq_source_service,
    get_service_factory,
)
from src.api_fastapi.opportunity.schemas import (
    OpportunityAdvanceQuery,
    OpportunityAdvanceRequest,
    OpportunityCreateFromEmailRequest,
    OpportunityCreateManualRequest,
    OpportunityQuery,
    OpportunitySearchQuery,
)
from src.domain.enums import OpportunityStage
from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.service.auth.auth_service import AuthService
from src.service.email.opportunity_from_email_service import OpportunityFromEmailService
from src.service.email.quote_send_service import QuoteSendService
from src.service.rfq.rfq_source_service import RfqSourceService

router = APIRouter(tags=["opportunity"])


def _serialize_opportunity(opportunity) -> dict:
    return jsonable_encoder(asdict(opportunity))


def _status_from_result(result: dict[str, Any], default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


def _resolve_user_id(authorization: str | None, auth_service: AuthService) -> str | None:
    is_valid, user_data = auth_service.verify_token(authorization or "")
    if not is_valid or not user_data:
        return None
    return user_data.get("id")


@router.get("/api/opportunity")
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


@router.get("/api/opportunity/advance")
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


@router.post("/api/opportunity/advance")
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


@router.get("/api/opportunities/search")
def opportunities_search(
    query: OpportunitySearchQuery = Depends(),
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    opportunity_repository: OpportunityRepository = Depends(get_opportunity_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = opportunity_repository.search_opportunities(
        user_id=user_id,
        source_reference_id=query.source_reference_id,
        name=query.name,
    )
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/opportunities/create-manual")
def opportunities_create_manual(
    payload: OpportunityCreateManualRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    opportunity_repository: OpportunityRepository = Depends(get_opportunity_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = opportunity_repository.create_opportunity_manual(
        user_id=user_id,
        name=payload.name,
    )
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/opportunities/create-from-email")
def opportunities_create_from_email(
    payload: OpportunityCreateFromEmailRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    opportunity_repository: OpportunityRepository = Depends(get_opportunity_repository),
    email_repository: EmailRepository = Depends(get_email_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    service = OpportunityFromEmailService(
        create_opportunity_from_email=email_repository.create_opportunity_from_email,
        generate_quote_for_opportunity=opportunity_repository.handle_generate_quote_for_opportunity,
    )
    result = service.create_opportunity_from_email(message_id=payload.message_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.delete("/api/opportunities/{opportunity_ids}")
def opportunities_delete(
    opportunity_ids: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    opportunity_repository: OpportunityRepository = Depends(get_opportunity_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ids_list = [raw_id.strip() for raw_id in opportunity_ids.split(",") if raw_id.strip()]
    result = opportunity_repository.delete_opportunities(opportunity_ids=ids_list, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/opportunity/{opportunity_id}/rfq/generate")
def opportunity_rfq_generate(
    opportunity_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    opportunity_repository: OpportunityRepository = Depends(get_opportunity_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = opportunity_repository.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/opportunity/{opportunity_id}/rfq/create-from-text")
async def opportunity_rfq_create_from_text(
    opportunity_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    rfq_source_service: RfqSourceService = Depends(get_rfq_source_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    content_type = request.headers.get("content-type", "")
    body = await request.body()

    result = rfq_source_service.create_rfq_source_from_html_body(
        opportunity_id=opportunity_id,
        body=body,
        content_type=content_type,
        user_id=user_id,
    )

    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/opportunity/{opportunity_id}/send-quote")
def opportunity_send_quote(
    opportunity_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    quote_send_service: QuoteSendService = Depends(get_quote_send_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = quote_send_service.handle_send_quote_for_opportunity(
        opportunity_id=opportunity_id,
        payload=payload,
        user_id=user_id,
    )
    return JSONResponse(result, status_code=_status_from_result(result))
