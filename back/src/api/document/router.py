"""FastAPI document router for document/contact flows."""

from typing import Any

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile
from fastapi.responses import JSONResponse

from src.api.dependencies import get_auth_service, get_database_repository, get_document_service
from src.api.document.schemas import (
    DocumentExtractRfpRequest,
    DocumentUpdateContentRequest,
    DocumentUpdateStatusRequest,
    DocumentUpdateStorageKeyRequest,
)
from src.repository.database.repository import DatabaseRepository
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


@router.get("/api/document")
def document_list(
    opportunity_id: str | None = Query(default=None),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if not opportunity_id:
        return JSONResponse({"error": "Missing opportunity_id"}, status_code=400)

    rows = db.execute_dict_query(
        """
        SELECT id,
               type,
               status,
               title,
               external_ref,
               currency,
               total_excl_tax,
               total_tax,
               total_incl_tax,
               storage_key,
               issued_at,
               received_at,
               created_at
        FROM document
        WHERE opportunity_id = %s
        ORDER BY created_at DESC
        """,
        (opportunity_id,),
    )
    return rows


@router.get("/api/invoice")
def invoice_list(
    opportunity_id: str | None = Query(default=None),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if not opportunity_id:
        return JSONResponse({"error": "Missing opportunity_id"}, status_code=400)

    rows = db.execute_dict_query(
        """
        SELECT id,
               opportunity_id,
               type,
               status,
               title,
               external_ref,
               currency,
               total_excl_tax,
               total_tax,
               total_incl_tax,
               storage_key,
               issued_at,
               received_at,
               created_at
        FROM document
        WHERE opportunity_id = %s
          AND type = 'INVOICE'
        ORDER BY created_at DESC
        """,
        (opportunity_id,),
    )
    return rows


@router.get("/api/invoice/{invoice_id}/view")
def invoice_get_view(
    invoice_id: str,
    opportunity_id: str | None = Query(default=None),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if not opportunity_id:
        return JSONResponse({"error": "Missing opportunity_id"}, status_code=400)

    invoice_rows = db.execute_dict_query(
        """
        SELECT id,
               opportunity_id,
               type,
               status,
               title,
               external_ref,
               currency,
               total_excl_tax,
               total_tax,
               total_incl_tax,
               storage_key,
               issued_at,
               received_at,
               created_at
        FROM document
        WHERE id = %s
          AND opportunity_id = %s
          AND type = 'INVOICE'
        LIMIT 1
        """,
        (invoice_id, opportunity_id),
    )
    if not invoice_rows:
        return JSONResponse({"error": "Invoice not found"}, status_code=404)

    sent_email_rows = db.execute_dict_query(
        """
        SELECT id,
               document_id,
               subject,
               body,
               from_email,
               to_emails,
               cc_emails,
               sent_at
        FROM sent_email
        WHERE document_id = %s
        ORDER BY sent_at DESC
        LIMIT 1
        """,
        (invoice_id,),
    )

    contact_rows = db.execute_dict_query(
        """
        SELECT c.id,
               c.account_id,
               c.name,
               c.email,
               c.phone,
               c.role_title,
               c.created_at
        FROM opportunity o
        JOIN contact c ON c.account_id = o.account_id
        WHERE o.id = %s
          AND c.email IS NOT NULL
          AND c.email <> ''
        ORDER BY c.created_at ASC
        LIMIT 1
        """,
        (opportunity_id,),
    )

    return {
        "invoice": invoice_rows[0],
        "sent_email": sent_email_rows[0] if sent_email_rows else None,
        "default_contact": contact_rows[0] if contact_rows else None,
    }


@router.get("/api/document/{document_id}")
def document_get(
    document_id: str,
    opportunity_id: str | None = Query(default=None),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if not opportunity_id:
        return JSONResponse({"error": "Missing opportunity_id"}, status_code=400)

    rows = db.execute_dict_query(
        """
        SELECT id,
               opportunity_id,
               type,
               status,
               title,
               external_ref,
               currency,
               total_incl_tax,
               storage_key,
               created_at
        FROM document
        WHERE id = %s
          AND opportunity_id = %s
        """,
        (document_id, opportunity_id),
    )
    if not rows:
        return JSONResponse({"error": "Document not found"}, status_code=404)

    document = rows[0]
    line_rows = db.execute_dict_query(
        """
        SELECT id,
               document_id,
               position,
               sku,
               brand,
               description,
               quantity,
               unit,
               unit_price_excl_tax,
               tax_rate,
               discount_rate,
               client_discount_rate,
               line_total_excl_tax
        FROM document_line
        WHERE document_id = %s
        ORDER BY position ASC
        """,
        (document_id,),
    )
    document["document_line"] = line_rows
    return document


@router.put("/api/document/{document_id}/storage-key")
def document_update_storage_key(
    document_id: str,
    payload: DocumentUpdateStorageKeyRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    rows = db.execute_dict_query(
        """
        UPDATE document
        SET storage_key = %s
        WHERE id = %s
        RETURNING id, opportunity_id, storage_key
        """,
        (payload.storage_key, document_id),
    )
    if not rows:
        return JSONResponse({"error": "Document not found"}, status_code=404)
    return rows[0]


@router.put("/api/document/{document_id}/status")
def document_update_status(
    document_id: str,
    payload: DocumentUpdateStatusRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    rows = db.execute_dict_query(
        """
        UPDATE document
        SET status = %s
        WHERE id = %s
        RETURNING id, opportunity_id, status
        """,
        (payload.status, document_id),
    )
    if not rows:
        return JSONResponse({"error": "Document not found"}, status_code=404)
    return rows[0]


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
