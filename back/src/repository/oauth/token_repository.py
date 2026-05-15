"""OAuth token persistence interface and placeholder implementation."""

from typing import Any, Dict, Optional


class OAuthTokenRepository:
    """Repository dedicated to OAuth token persistence."""

    def get_tokens(self, provider: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Return tokens for provider/user, or None if missing."""
        raise NotImplementedError()

    def save_tokens(self, provider: str, user_id: str, tokens: Dict[str, Any]) -> None:
        """Persist tokens for provider/user."""
        raise NotImplementedError()

