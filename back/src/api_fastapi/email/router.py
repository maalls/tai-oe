"""FastAPI email router delegating to existing email handlers."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.email.handler import EmailHandlers
from src.api_fastapi.dependencies import get_email_handlers
from src.api_fastapi.email.schemas import (
    GmailAuthorizeQuery,
    GmailOauthStartQuery,
    GmailStatusQuery,
    GmailUserQuery,
)

router = APIRouter(tags=["email"])


def _status_from_result(result: dict[str, Any], default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


@router.get("/api/gmail/status")
def gmail_status(
    query: GmailStatusQuery = Depends(),
    email_handlers: EmailHandlers = Depends(get_email_handlers),
):
    result = email_handlers.get_gmail_status(user_id=query.user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/authorize")
def gmail_authorize(
    query: GmailAuthorizeQuery = Depends(),
    email_handlers: EmailHandlers = Depends(get_email_handlers),
):
    result = email_handlers.handle_gmail_authorize(redirect_url=query.redirect_url)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/oauth/start")
def gmail_oauth_start(
    query: GmailOauthStartQuery = Depends(),
    email_handlers: EmailHandlers = Depends(get_email_handlers),
):
    result = email_handlers.get_gmail_oauth_url(query.redirect_url, user_id=query.user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/revoke")
def gmail_revoke(
    query: GmailUserQuery = Depends(),
    email_handlers: EmailHandlers = Depends(get_email_handlers),
):
    result = email_handlers.revoke_gmail(user_id=query.user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/profile")
def gmail_profile(
    query: GmailUserQuery = Depends(),
    email_handlers: EmailHandlers = Depends(get_email_handlers),
):
    result = email_handlers.get_gmail_profile(user_id=query.user_id)
    return JSONResponse(result, status_code=_status_from_result(result))
