"""FastAPI quote router delegating to quote service/controller layer."""

from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, Response

from src.api.dependencies import get_auth_service, get_invoice_handlers, get_quote_controller, get_quote_send_service
from src.api.quote.schemas import QuoteDownloadQuery, QuoteSendRequest, QuoteSubmitRequest, QuoteUpdateRequest
from src.service.auth.auth_service import AuthService
from src.service.email.quote_send_service import QuoteSendService
from src.service.invoice.invoice_service import InvoiceService
from src.service.quote.quote_controller import QuoteController

router = APIRouter(tags=["quote"])


def _status_from_result(result: dict[str, Any], default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


def _resolve_user_id(
    authorization: str | None,
    auth_service: AuthService,
) -> str | None:
    is_valid, user_data = auth_service.verify_token(authorization or "")
    if not is_valid or not user_data:
        return None
    return user_data.get("id")


@router.post("/api/quote")
def quote_submit(payload: QuoteSubmitRequest, quote_controller: QuoteController = Depends(get_quote_controller)):
    result = quote_controller.handle_quote_submit(payload.model_dump())
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/quote/send")
def quote_send(
    payload: QuoteSendRequest,
    quote_send_service: QuoteSendService = Depends(get_quote_send_service),
):
    result = quote_send_service.handle_quote_send(
        body=payload.model_dump_json().encode("utf-8"),
        content_type="application/json",
    )
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/quote/{document_id}")
def quote_update(
    document_id: str,
    payload: QuoteUpdateRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    quote_controller: QuoteController = Depends(get_quote_controller),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = quote_controller.update(document_id=document_id, payload=payload.model_dump(), user_id=user_id)
    status = 400 if result.get("error") else 200
    return JSONResponse(result, status_code=status)


@router.get("/api/quotes/list")
def quotes_list(quote_controller: QuoteController = Depends(get_quote_controller)):
    result = quote_controller.handle_list_quotes()
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/quote/{document_id}/pdf")
def quote_generate_pdf(
    document_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    quote_controller: QuoteController = Depends(get_quote_controller),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = quote_controller.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/quote/{opportunity_id}/generate")
def quote_generate_from_opportunity(
    opportunity_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    quote_controller: QuoteController = Depends(get_quote_controller),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = quote_controller.handle_generate_quote_pdf_from_opportunity(opportunity_id=opportunity_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/quote/{quote_id}/invoice")
def quote_generate_invoice(
    quote_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    invoice_handlers: InvoiceService = Depends(get_invoice_handlers),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = invoice_handlers.handle_generate_invoice_from_quote(quote_id=quote_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/invoice/{invoice_id}/pdf")
def invoice_generate_pdf(
    invoice_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    invoice_handlers: InvoiceService = Depends(get_invoice_handlers),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = invoice_handlers.handle_generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/invoice/{invoice_id}/send")
def invoice_send(
    invoice_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    invoice_handlers: InvoiceService = Depends(get_invoice_handlers),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = invoice_handlers.handle_send_invoice(invoice_id=invoice_id, payload=payload, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/quotes/download/{filename}")
def quote_download(
    filename: str,
    query: QuoteDownloadQuery = Depends(),
    quote_controller: QuoteController = Depends(get_quote_controller),
):
    is_inline = query.inline == 1

    try:
        content = quote_controller.handle_get_quote_file(filename)
        disposition = "inline" if is_inline else "attachment"
        return Response(
            content=content,
            status_code=200,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'{disposition}; filename="{filename}"',
                "Content-Length": str(len(content)),
            },
        )
    except FileNotFoundError:
        return JSONResponse({"error": "Quote file not found"}, status_code=404)
    except Exception as exc:
        return JSONResponse({"error": f"Error streaming PDF: {exc}"}, status_code=500)
