"""Dependency providers for FastAPI routers."""

from src.api.email.handler import EmailHandlers
from src.service.auth.auth_service import AuthService
from src.service.auth.oauth_service import OAuthService


def get_auth_service() -> AuthService:
    return AuthService()


def get_oauth_service() -> OAuthService:
    return OAuthService()


def get_email_handlers() -> EmailHandlers:
    return EmailHandlers()
