"""FastAPI email router delegating to provider services."""

from typing import Any, Callable

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, RedirectResponse, Response

from src.api.dependencies import get_auth_service, get_gmail_service, get_outlook_service
from src.api.email.schemas import (
    GmailAuthorizeQuery,
    GmailClassifyQuery,
    EmailResyncRequest,
    ImapConfigRequest,
    ProviderMessagesQuery,
    ProviderOauthCallbackQuery,
    ProviderOauthStartQuery,
    ProviderStatusQuery,
    ProviderUserQuery,
)
from src.service.auth.auth_service import AuthService
from src.service.email.base import EmailProviderService
from src.service.email.gmail_service import GmailService

router = APIRouter(tags=["email"])


def _status_from_result(result: dict[str, Any], default_status: int = 200) -> int:
    raw_status = result.get("status")
    if isinstance(raw_status, int):
        return raw_status
    if raw_status == "error":
        return 400
    return default_status


def _resolve_user_id(
    explicit_user_id: str | None,
    authorization: str | None,
    auth_service: AuthService,
) -> str | None:
    if explicit_user_id:
        return explicit_user_id
    is_valid, user_data = auth_service.verify_token(authorization or "")
    if not is_valid or not user_data:
        return None
    return user_data.get("id")


def make_email_provider_router(
    prefix: str,
    get_service: Callable[[], EmailProviderService],
    callback_aliases: list[str] | None = None,
) -> APIRouter:
    provider_router = APIRouter(tags=["email"])

    @provider_router.get(f"/api/{prefix}/status")
    def status(
        query: ProviderStatusQuery = Depends(),
        service: EmailProviderService = Depends(get_service),
    ):
        result = service.get_status(user_id=query.user_id)
        return JSONResponse(result, status_code=_status_from_result(result))

    @provider_router.get(f"/api/{prefix}/oauth/start")
    def oauth_start(
        query: ProviderOauthStartQuery = Depends(),
        service: EmailProviderService = Depends(get_service),
    ):
        result = service.get_oauth_url(query.redirect_url, user_id=query.user_id)
        return JSONResponse(result, status_code=_status_from_result(result))

    @provider_router.api_route(f"/api/{prefix}/revoke", methods=["GET", "POST"])
    def revoke(
        query: ProviderUserQuery = Depends(),
        service: EmailProviderService = Depends(get_service),
    ):
        result = service.revoke(user_id=query.user_id)
        return JSONResponse(result, status_code=_status_from_result(result))

    @provider_router.get(f"/api/{prefix}/profile")
    def profile(
        query: ProviderUserQuery = Depends(),
        service: EmailProviderService = Depends(get_service),
    ):
        result = service.get_profile(user_id=query.user_id)
        return JSONResponse(result, status_code=_status_from_result(result))

    @provider_router.get(f"/api/{prefix}/oauth/callback")
    def oauth_callback(
        query: ProviderOauthCallbackQuery = Depends(),
        service: EmailProviderService = Depends(get_service),
    ):
        result = service.oauth_callback(code=query.code, state=query.state)
        if result.get("status") == "ok":
            redirect_url = result.get("redirect_url") or "http://localhost:5173/settings"
            return RedirectResponse(url=redirect_url, status_code=302)
        return JSONResponse(result, status_code=500)

    @provider_router.get(f"/api/{prefix}/messages")
    def messages(
        query: ProviderMessagesQuery = Depends(),
        authorization: str | None = Header(default=None),
        service: EmailProviderService = Depends(get_service),
        auth_service: AuthService = Depends(get_auth_service),
    ):
        user_id = _resolve_user_id(query.user_id, authorization, auth_service)
        if not user_id:
            return JSONResponse({"status": "error", "message": "Missing user_id"}, status_code=400)

        result = service.list_messages(user_id=user_id, max_results=query.max_results, force=query.force)
        return JSONResponse(result, status_code=_status_from_result(result))

    for alias in callback_aliases or []:
        provider_router.add_api_route(
            f"/api/{alias}/oauth/callback",
            oauth_callback,
            methods=["GET"],
        )

    return provider_router


router.include_router(make_email_provider_router("gmail", get_gmail_service, callback_aliases=["google"]))
router.include_router(make_email_provider_router("outlook", get_outlook_service))


@router.get("/api/gmail/authorize")
def gmail_authorize(
    query: GmailAuthorizeQuery = Depends(),
    gmail_service: GmailService = Depends(get_gmail_service),
):
    result = gmail_service.authorize(redirect_url=query.redirect_url)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/classify-unclassified")
def gmail_classify_unclassified(
    query: GmailClassifyQuery = Depends(),
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(query.user_id, authorization, auth_service)
    if not user_id:
        return JSONResponse({"status": "error", "message": "Missing user_id"}, status_code=400)

    result = gmail_service.classify_unclassified(user_id=user_id, limit=query.limit)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/gmail/message/{message_id}")
def gmail_message_body(
    message_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    result = gmail_service.get_message_body(message_id=message_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/emails/classify/{email_id}")
def email_classify(
    email_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.classify_email(email_id=email_id, user_id=user_id, force=True)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/email/{email_id}/resync")
def email_resync(
    email_id: str,
    payload: EmailResyncRequest,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.resync_email(
        email_id=email_id,
        provider_message_id=payload.provider_message_id,
        user_id=user_id,
    )
    return JSONResponse(result, status_code=_status_from_result(result))


@router.delete("/api/email/{email_id}")
def email_delete(
    email_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.delete_email(email_id=email_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/email/{email_id}/attachments")
def email_attachments_list(
    email_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.list_attachments(email_id=email_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.delete("/api/email-attachment/{attachment_id}")
def email_attachment_delete(
    attachment_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.delete_attachment(attachment_id=attachment_id, user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/email-attachment/{attachment_id}/download")
def email_attachment_download(
    attachment_id: str,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    status_code, headers, file_content = gmail_service.download_attachment(attachment_id=attachment_id, user_id=user_id)
    return Response(content=file_content, status_code=status_code, headers=headers)


@router.get("/api/imap/status")
def imap_status(
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.get_imap_status(user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.get("/api/imap/config")
def imap_config_get(
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.get_imap_config(user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/imap/config")
def imap_config_post(
    payload: ImapConfigRequest,
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.save_imap_config(user_id=user_id, payload=payload.model_dump())
    return JSONResponse(result, status_code=_status_from_result(result))


@router.post("/api/imap/test")
def imap_test(
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.test_imap_connection(user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))


@router.delete("/api/imap/config")
def imap_config_delete(
    authorization: str | None = Header(default=None),
    gmail_service: GmailService = Depends(get_gmail_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = _resolve_user_id(None, authorization, auth_service)
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    result = gmail_service.clear_imap_config(user_id=user_id)
    return JSONResponse(result, status_code=_status_from_result(result))
