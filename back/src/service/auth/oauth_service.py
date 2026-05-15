"""OAuth orchestration service.

This module centralizes provider-agnostic login/callback orchestration.
"""

from typing import Any, Dict, Optional

from src.infrastructure.clients.oauth.azure_client import (
    get_azure_oauth_url,
    handle_azure_oauth_callback,
)


class OAuthService:
    """Orchestrate OAuth login/callback workflows."""

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        p = (provider or "").strip().lower()
        if p in {"azure", "microsoft", "ms"}:
            return "azure"
        return p

    def build_login_url(self, provider: str, redirect_url: Optional[str] = None) -> Dict[str, Any]:
        """Build provider login URL and state."""
        normalized = self._normalize_provider(provider)

        if normalized == "azure":
            return get_azure_oauth_url(redirect_url=redirect_url)

        return {
            "status": "error",
            "message": f"Unsupported OAuth provider: {provider}",
        }

    def exchange_callback(self, provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Exchange callback code for tokens and return normalized payload."""
        normalized = self._normalize_provider(provider)

        if normalized == "azure":
            return handle_azure_oauth_callback(code=code, state=state)

        return {
            "status": "error",
            "message": f"Unsupported OAuth provider: {provider}",
        }

