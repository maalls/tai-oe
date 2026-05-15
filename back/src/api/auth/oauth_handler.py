"""API transport layer for OAuth endpoints.

This module is intentionally thin: parse/validate HTTP params and delegate
business flow to service.auth.oauth_service.OAuthService.
"""

from typing import Any, Dict, Optional

from src.service.auth.oauth_service import OAuthService


class OAuthHandler:
    """HTTP-oriented OAuth handler."""

    def __init__(self, oauth_service: Optional[OAuthService] = None):
        self.oauth_service = oauth_service or OAuthService()

    def handle_login(self, provider: str, redirect_url: Optional[str] = None) -> Dict[str, Any]:
        """Handle OAuth login endpoint."""
        if not provider:
            return {"status": "error", "message": "Missing OAuth provider"}
        return self.oauth_service.build_login_url(provider=provider, redirect_url=redirect_url)

    def handle_callback(self, provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Handle OAuth callback endpoint."""
        if not provider:
            return {"status": "error", "message": "Missing OAuth provider"}
        if not code:
            return {"status": "error", "message": "Missing OAuth code"}
        return self.oauth_service.exchange_callback(provider=provider, code=code, state=state)

