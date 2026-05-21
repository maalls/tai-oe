"""OAuth token persistence repository."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.infrastructure.clients.supabase import get_supabase_service


class OAuthTokenRepository:
    """Repository dedicated to OAuth token persistence."""

    def get_token_json(self, user_id: str, provider: str, service: str) -> Optional[str]:
        try:
            response = (
                get_supabase_service()
                .table("oauth_tokens")
                .select("token_json")
                .eq("user_id", user_id)
                .eq("provider", provider)
                .eq("service", service)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0].get("token_json")
        except Exception as exc:
            print(f"[OAuthTokenRepository] Error reading oauth token ({provider}/{service}): {exc}")
        return None

    def set_token_json(
        self,
        user_id: str,
        provider: str,
        service: str,
        token_json: str,
        scope: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> bool:
        try:
            payload = {
                "user_id": user_id,
                "provider": provider,
                "service": service,
                "token_json": token_json,
                "scope": scope,
                "expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            response = (
                get_supabase_service()
                .table("oauth_tokens")
                .upsert(payload, on_conflict="user_id,provider,service")
                .execute()
            )
            return bool(response.data)
        except Exception as exc:
            print(f"[OAuthTokenRepository] Error saving oauth token ({provider}/{service}): {exc}")
            return False

    def clear_token(self, user_id: str, provider: str, service: str) -> bool:
        try:
            (
                get_supabase_service()
                .table("oauth_tokens")
                .delete()
                .eq("user_id", user_id)
                .eq("provider", provider)
                .eq("service", service)
                .execute()
            )
            return True
        except Exception as exc:
            print(f"[OAuthTokenRepository] Error clearing oauth token ({provider}/{service}): {exc}")
            return False

    def get_tokens(self, provider: str, user_id: str, service: str = "mail") -> Optional[Dict[str, Any]]:
        token_json = self.get_token_json(user_id=user_id, provider=provider, service=service)
        if not token_json:
            return None
        try:
            return json.loads(token_json)
        except Exception:
            return None

    def save_tokens(self, provider: str, user_id: str, tokens: Dict[str, Any], service: str = "mail") -> bool:
        expires_at = tokens.get("expires_at") if isinstance(tokens, dict) else None
        scope = tokens.get("scope") if isinstance(tokens, dict) else None
        return self.set_token_json(
            user_id=user_id,
            provider=provider,
            service=service,
            token_json=json.dumps(tokens),
            scope=scope,
            expires_at=expires_at,
        )

