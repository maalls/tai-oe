"""OAuth state persistence interface and placeholder implementation."""

from typing import Optional


class OAuthStateRepository:
    """Repository dedicated to OAuth state creation/validation."""

    def create_state(self, provider: str, redirect_url: Optional[str] = None) -> str:
        """Create and persist an OAuth state token."""
        raise NotImplementedError()

    def validate_state(self, state: str) -> bool:
        """Validate a previously issued OAuth state token."""
        raise NotImplementedError()

