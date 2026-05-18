"""FastAPI opportunity router."""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    get_auth_service,
    get_email_repository,
    get_opportunity_repository,
    get_quote_send_service,
    get_rfq_source_service,
    get_service_factory,
)
from src.api.opportunity.schemas import (
    OpportunityAdvanceQuery,
    OpportunityAdvanceRequest,
    OpportunityCreateFromEmailRequest,
    OpportunityExtractAuthorContactRequest,
    OpportunityCreateManualRequest,
    OpportunityQuery,
    OpportunitySearchQuery,
    OpportunityStageHistoryQuery,
    OpportunityUpdateStageStateRequest,
    OpportunityUpdateNameRequest,
)
from src.domain.enums import OpportunityStage
from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.repository.database.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService
from src.service.email.opportunity_from_email_service import OpportunityFromEmailService
from src.service.email.quote_send_service import QuoteSendService
from src.service.rfq.rfq_source_service import RfqSourceService

router = APIRouter(tags=["opportunity"])


def get_db():
    return DatabaseRepository()


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


@router.get("/api/opportunity/{opportunity_id}/source")
def get_opportunity_source(opportunity_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, source, source_reference_id
        FROM opportunity
        WHERE id = %s
        """,
        (opportunity_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opportunity = rows[0]
    source_type = opportunity.get("source")
    source_reference_id = opportunity.get("source_reference_id")

    participants_rows = db.execute_dict_query(
        """
        SELECT op.role,
               op.contact_id,
               c.id AS contact_id_ref,
               c.name AS contact_name,
               c.email AS contact_email
        FROM opportunity_participant op
        LEFT JOIN contact c ON c.id = op.contact_id
        WHERE op.opportunity_id = %s
        """,
        (opportunity_id,),
    )
    participants = [
        {
            "role": row.get("role"),
            "contact_id": row.get("contact_id"),
            "contact": {
                "id": row.get("contact_id_ref"),
                "name": row.get("contact_name"),
                "email": row.get("contact_email"),
            }
            if row.get("contact_id_ref")
            else None,
        }
        for row in participants_rows
    ]

    source_email = None
    source_document = None
    attachments = []

    if source_type == "email" and source_reference_id:
        email_rows = db.execute_dict_query(
            "SELECT * FROM email WHERE id = %s",
            (source_reference_id,),
        )
        source_email = email_rows[0] if email_rows else None
        if source_email and source_email.get("id"):
            attachments = db.execute_dict_query(
                """
                SELECT id, filename, mime_type, size, storage_path
                FROM email_attachment
                WHERE email_id = %s
                """,
                (source_email["id"],),
            )
    elif source_type in ("rfp_upload", "user_form") and source_reference_id:
        document_rows = db.execute_dict_query(
            "SELECT * FROM document WHERE id = %s",
            (source_reference_id,),
        )
        source_document = document_rows[0] if document_rows else None
        attachments = db.execute_dict_query(
            """
            SELECT id, title, storage_key, created_at
            FROM document
            WHERE opportunity_id = %s
              AND type = 'ATTACHMENT'
            """,
            (opportunity_id,),
        )

    return {
        "source_type": source_type,
        "email": source_email,
        "document": source_document,
        "participants": participants,
        "attachments": attachments,
    }


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


@router.get("/api/opportunity/{opportunity_id}/stage-history")
def get_opportunity_stage_history(
    opportunity_id: str,
    query: OpportunityStageHistoryQuery = Depends(),
    db=Depends(get_db),
):
    capped_limit = max(1, min(query.limit, 50))
    rows = db.execute_dict_query(
        """
        SELECT opportunity_id,
               from_stage,
               to_stage,
               changed_by,
               changed_at
        FROM opportunity_state_transition
        WHERE opportunity_id = %s
        ORDER BY changed_at DESC
        LIMIT %s
        """,
        (opportunity_id, capped_limit),
    )
    return rows


@router.put("/api/opportunity/{opportunity_id}/stage-state")
def update_opportunity_stage_state(
    opportunity_id: str,
    payload: OpportunityUpdateStageStateRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db=Depends(get_db),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    current_rows = db.execute_dict_query(
        "SELECT stage, status FROM opportunity WHERE id = %s",
        (opportunity_id,),
    )
    if not current_rows:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    current_stage = current_rows[0].get("stage")
    rows = db.execute_dict_query(
        """
        UPDATE opportunity
        SET stage = %s,
            status = %s,
            updated_at = now()
        WHERE id = %s
        RETURNING id, stage, status
        """,
        (payload.stage, payload.status, opportunity_id),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db.execute_dict_query(
        """
        INSERT INTO opportunity_state_transition (
            opportunity_id,
            from_stage,
            to_stage,
            changed_by,
            changed_at
        )
        VALUES (%s, %s, %s, %s, now())
        """,
        (opportunity_id, current_stage, payload.stage, user_id),
    )

    return rows[0]


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


@router.put("/api/opportunity/{opportunity_id}/name")
def opportunity_update_name(
    opportunity_id: str,
    payload: OpportunityUpdateNameRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db=Depends(get_db),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    trimmed_name = (payload.name or "").strip()
    rows = db.execute_dict_query(
        """
        UPDATE opportunity
        SET name = %s, updated_at = now()
        WHERE id = %s
        RETURNING id, account_id, name
        """,
        (trimmed_name, opportunity_id),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return rows[0]


@router.post("/api/opportunity/{opportunity_id}/extract-author-contact")
def opportunity_extract_author_contact(
    opportunity_id: str,
    payload: OpportunityExtractAuthorContactRequest,
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db=Depends(get_db),
):
    user_id = _resolve_user_id(authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    rows = db.execute_dict_query(
        "SELECT id, account_id FROM opportunity WHERE id = %s",
        (opportunity_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    account_id = rows[0].get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="Opportunity has no account")

    email_value = payload.from_email.strip().lower()
    existing_contact_rows = db.execute_dict_query(
        """
        SELECT id
        FROM contact
        WHERE email = %s AND account_id = %s
        LIMIT 1
        """,
        (email_value, account_id),
    )

    if existing_contact_rows:
        contact_id = existing_contact_rows[0]["id"]
        db.execute_dict_query(
            "UPDATE contact SET name = %s WHERE id = %s",
            ((payload.from_name or email_value), contact_id),
        )
    else:
        created_contact_rows = db.execute_dict_query(
            """
            INSERT INTO contact (account_id, name, email)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (account_id, (payload.from_name or email_value), email_value),
        )
        contact_id = created_contact_rows[0]["id"]

    existing_participant_rows = db.execute_dict_query(
        """
        SELECT opportunity_id, contact_id
        FROM opportunity_participant
        WHERE opportunity_id = %s AND contact_id = %s
        LIMIT 1
        """,
        (opportunity_id, contact_id),
    )
    linked = bool(existing_participant_rows)
    if not linked:
        db.execute_dict_query(
            """
            INSERT INTO opportunity_participant (opportunity_id, contact_id, role)
            VALUES (%s, %s, %s)
            """,
            (opportunity_id, contact_id, "BUYER"),
        )
        linked = True

    return {
        "status": "ok",
        "contact_id": contact_id,
        "linked": linked,
    }


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


@router.get("/api/opportunity/{opportunity_id}/sent-email")
def opportunity_get_sent_email(
    opportunity_id: str,
    document_id: str | None = None,
    db=Depends(get_db),
):
    target_document_id = document_id

    if not target_document_id:
        quote_rows = db.execute_dict_query(
            """
            SELECT id
            FROM document
            WHERE opportunity_id = %s
              AND type = 'QUOTE'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (opportunity_id,),
        )
        if not quote_rows:
            return {"sent_email": None}
        target_document_id = quote_rows[0].get("id")

    rows = db.execute_dict_query(
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
        (target_document_id,),
    )
    return {"sent_email": rows[0] if rows else None}
