"""FastAPI auth router delegating to service layer auth modules."""

from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.auth.schemas import LoginRequest, OAuthCallbackQuery, OAuthLoginQuery, SignupRequest
from src.api.dependencies import get_auth_service, get_database_repository, get_oauth_service
from src.repository.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService
from src.service.auth.oauth_service import OAuthService

router = APIRouter(tags=["auth"])


def _pop_status(result: dict[str, Any], default_status: int = 200) -> tuple[dict[str, Any], int]:
    payload = dict(result)
    raw_status = payload.pop("status", default_status)

    if isinstance(raw_status, int):
        return payload, raw_status
    if raw_status == "ok":
        return payload, 200
    if raw_status == "error":
        return payload, 400
    return payload, default_status


@router.post("/api/auth/signup")
def auth_signup(
    body: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = auth_service.signup(email=body.email, password=body.password)
    payload, status = _pop_status(result, default_status=201)
    return JSONResponse(payload, status_code=status)


@router.post("/api/auth/login")
def auth_login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    result = auth_service.login(email=body.email, password=body.password)
    payload, status = _pop_status(result, default_status=200)
    return JSONResponse(payload, status_code=status)


@router.post("/api/auth/logout")
def auth_logout(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    result = auth_service.logout(authorization or "")
    payload, status = _pop_status(result, default_status=200)
    return JSONResponse(payload, status_code=status)


@router.get("/api/auth/user")
def auth_user(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    result = auth_service.get_user(authorization or "")
    user_payload = result.get("user") if isinstance(result.get("user"), dict) else None
    if user_payload and user_payload.get("id"):
        profile = db.fetch_profile(user_payload["id"]) or {}
        user_payload["role"] = profile.get("role") or "user"
    payload, status = _pop_status(result, default_status=200)
    return JSONResponse(payload, status_code=status)


@router.get("/api/oauth/login")
def oauth_login(
    query: OAuthLoginQuery = Depends(),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    result = oauth_service.build_login_url(provider=query.provider, redirect_url=query.redirect_url)
    payload, status = _pop_status(result, default_status=200)
    return JSONResponse(payload, status_code=status)


@router.get("/api/oauth/callback")
def oauth_callback(
    query: OAuthCallbackQuery = Depends(),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    result = oauth_service.exchange_callback(
        provider=query.provider,
        code=query.code,
        state=query.state,
    )
    if result.get("status") == "ok" and result.get("redirect_url"):
        return RedirectResponse(url=result["redirect_url"], status_code=302)

    payload, status = _pop_status(result, default_status=200)
    return JSONResponse(payload, status_code=status)
