"""FastAPI RFQ router for upload and draft generation endpoints."""

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_auth_service, get_rfq_handlers
from src.api_fastapi.rfq.schemas import RfqGenerateRequest
from src.service.auth.auth_service import AuthService
from src.service.rfq.rfq_service import RfqService

router = APIRouter(tags=["rfq"])


def _status_from_result(result: dict, default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


@router.post("/api/rfq/generate")
def rfq_generate(
    payload: RfqGenerateRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    rfq_handlers: RfqService = Depends(get_rfq_handlers),
):
    is_valid, user_data = auth_service.verify_token(authorization or "")
    if not is_valid or not user_data:
        return JSONResponse({"error_code": "UNAUTHORIZED", "message": "Unauthorized"}, status_code=401)

    text = payload.text or payload.content
    message_id = payload.message_id
    user_id = user_data.get("id")

    result = rfq_handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/rfp")
async def rfp_upload(
    request: Request,
    rfq_handlers: RfqService = Depends(get_rfq_handlers),
):
    content_type = request.headers.get("content-type", "")
    body = await request.body()

    result = rfq_handlers.handle_rfp_upload(body=body, content_type=content_type)
    return JSONResponse(result, status_code=_status_from_result(result))
