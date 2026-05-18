"""Dependency providers for FastAPI routers."""

from pathlib import Path

from src.service.auth.auth_service import AuthService
from src.service.auth.oauth_service import OAuthService
from src.service.email.gmail_service import GmailService
from src.service.utility.utility_service import UtilityService


def get_auth_service() -> AuthService:
    return AuthService()


def get_oauth_service() -> OAuthService:
    return OAuthService()


def get_gmail_service() -> GmailService:
    return GmailService()


def get_utility_service() -> UtilityService:
    src_dir = Path(__file__).resolve().parents[1]
    base_dir = src_dir.parents[1]
    prompt_base_dir = src_dir / "infrastructure" / "prompts"
    return UtilityService(base_dir=base_dir, prompt_base_dir=prompt_base_dir)
