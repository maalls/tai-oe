"""FastAPI document router for document/contact flows."""

from typing import Any

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile
from fastapi.responses import JSONResponse

from src.api_fastapi.dependencies import get_auth_service, get_document_service
from src.api_fastapi.document.schemas import DocumentExtractRfpRequest, DocumentUpdateContentRequest
from src.service.auth.auth_service import AuthService
from src.service.document.document_service import DocumentService

router = APIRouter(tags=["document"])


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


@router.post("/api/document/extract-rfp")
def document_extract_rfp(
    payload: DocumentExtractRfpRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    document_service: DocumentService = Depends(get_document_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = document_service.handle_extract_rfp_from_document(document_id=payload.document_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/document/update-content")
def document_update_content(
    payload: DocumentUpdateContentRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    document_service: DocumentService = Depends(get_document_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = document_service.handle_update_document_content(
        document_id=payload.document_id,
        content=payload.content,
        user_id=user_id,
    )
    return JSONResponse(result, status_code=_status_from_result(result))


@router.delete("/api/document/{document_id}")
def document_delete(
    document_id: str,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    document_service: DocumentService = Depends(get_document_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = document_service.handle_delete_document(document_id=document_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/chat/attachments")
async def chat_attachments_upload(
    opportunity_id: str = Query(default=""),
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    document_service: DocumentService = Depends(get_document_service),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    file_content = await file.read()
    result = document_service.handle_chat_attachment_upload(
        filename=file.filename or "upload.bin",
        file_content=file_content,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_content),
        user_id=user_id,
        opportunity_id=opportunity_id,
    )
    return JSONResponse(result, status_code=_status_from_result(result))
