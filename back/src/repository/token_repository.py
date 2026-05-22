"""OAuth token persistence repository."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler


class OAuthTokenRepository:
    """Repository dedicated to OAuth token persistence."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    @staticmethod
    def _normalize_expires_at(expires_at: Any) -> Optional[str]:
        if expires_at is None:
            return None

        if isinstance(expires_at, (int, float)):
            return datetime.fromtimestamp(float(expires_at), tz=timezone.utc).isoformat()

        if isinstance(expires_at, str):
            raw = expires_at.strip()
            if not raw:
                return None
            if raw.isdigit():
                return datetime.fromtimestamp(float(raw), tz=timezone.utc).isoformat()
            return raw

        return str(expires_at)

    def get_token_json(self, user_id: str, provider: str, service: str) -> Optional[str]:
        try:
            rows = self._get_db_handler().execute_dict_query(
                """
                SELECT token_json
                FROM oauth_tokens
                WHERE user_id = %s AND provider = %s AND service = %s
                LIMIT 1
                """,
                (user_id, provider, service),
            )
            if rows:
                return rows[0].get("token_json")
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
        expires_at: Optional[Any] = None,
    ) -> bool:
        try:
            payload = {
                "user_id": user_id,
                "provider": provider,
                "service": service,
                "token_json": token_json,
                "scope": scope,
                "expires_at": self._normalize_expires_at(expires_at),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            rows = self._get_db_handler().execute_dict_query(
                """
                INSERT INTO oauth_tokens (
                    user_id,
                    provider,
                    service,
                    token_json,
                    scope,
                    expires_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, provider, service)
                DO UPDATE SET
                    token_json = EXCLUDED.token_json,
                    scope = EXCLUDED.scope,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = EXCLUDED.updated_at
                RETURNING user_id
                """,
                (
                    payload["user_id"],
                    payload["provider"],
                    payload["service"],
                    payload["token_json"],
                    payload["scope"],
                    payload["expires_at"],
                    payload["updated_at"],
                ),
            )
            return bool(rows)
        except Exception as exc:
            print(f"[OAuthTokenRepository] Error saving oauth token ({provider}/{service}): {exc}")
            return False

    def clear_token(self, user_id: str, provider: str, service: str) -> bool:
        try:
            rows_affected = self._get_db_handler().execute_update(
                "DELETE FROM oauth_tokens WHERE user_id = %s AND provider = %s AND service = %s",
                (user_id, provider, service),
            )
            return rows_affected >= 0
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

