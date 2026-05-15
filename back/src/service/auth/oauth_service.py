"""OAuth orchestration service.

This module centralizes provider-agnostic login/callback orchestration.
"""

from typing import Any, Dict, Optional


class OAuthService:
    """Orchestrate OAuth login/callback workflows."""

    def build_login_url(self, provider: str, redirect_url: Optional[str] = None) -> Dict[str, Any]:
        """Build provider login URL and state."""
        raise NotImplementedError()

    def exchange_callback(self, provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Exchange callback code for tokens and return normalized payload."""
        raise NotImplementedError()

