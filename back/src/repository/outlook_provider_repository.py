"""Outlook provider repository for OAuth/profile operations."""

import json
from typing import Any, Dict, Optional

from src.infrastructure.clients.outlook_client import (
    _oauth_settings,
    get_outlook_oauth_url,
    handle_outlook_oauth_callback,
    OutlookClient,
)
from src.repository.token_repository import OAuthTokenRepository


class OutlookProviderRepository:
    """Repository dedicated to Outlook OAuth and profile interactions."""

    PROVIDER = "microsoft"
    SERVICE = "mail"

    def __init__(self, oauth_token_repository: Optional[OAuthTokenRepository] = None):
        self.oauth_token_repository = oauth_token_repository or OAuthTokenRepository()

    def _save_outlook_token(self, user_id: str, token_dict: Dict[str, Any]) -> bool:
        return self.oauth_token_repository.set_token_json(
            user_id=user_id,
            provider=self.PROVIDER,
            service=self.SERVICE,
            token_json=json.dumps(token_dict),
            scope=token_dict.get("scope"),
            expires_at=token_dict.get("expires_at"),
        )

    def _get_outlook_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        token_json = self.oauth_token_repository.get_token_json(
            user_id=user_id,
            provider=self.PROVIDER,
            service=self.SERVICE,
        )
        if not token_json:
            return None

        try:
            return json.loads(token_json)
        except Exception as exc:
            print(f"[OutlookProviderRepository] Error parsing outlook token JSON: {exc}")
            return None

    def _get_outlook_client(self, user_id: str) -> tuple[Optional[OutlookClient], Optional[Dict[str, str]]]:
        token_dict = self._get_outlook_token(user_id)
        if not token_dict:
            return None, {
                "status": "error",
                "error_code": "OUTLOOK_NOT_AUTHORIZED",
                "message": "Outlook not authorized. Please authorize first.",
            }

        settings = _oauth_settings()
        client_id = settings.get("client_id")
        client_secret = settings.get("client_secret")
        tenant = settings.get("tenant")

        if not client_id or not client_secret:
            return None, {
                "status": "error",
                "error_code": "OUTLOOK_NOT_CONFIGURED",
                "message": "Missing AZUR_CLIENT_ID or AZUR_CLIENT_SECRET",
            }

        access_token = token_dict.get("access_token")
        if not access_token:
            return None, {
                "status": "error",
                "error_code": "OUTLOOK_NOT_AUTHORIZED",
                "message": "Outlook token is missing access_token",
            }

        token_saver = lambda tokens: self._save_outlook_token(user_id, tokens)

        client = OutlookClient(
            access_token=access_token,
            refresh_token=token_dict.get("refresh_token"),
            expires_at=int(token_dict.get("expires_at", 0)),
            client_id=client_id,
            client_secret=client_secret,
            tenant=tenant or "common",
            token_saver=token_saver,
        )
        return client, None

    def get_outlook_oauth_url(self, redirect_url: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        return get_outlook_oauth_url(redirect_url=redirect_url, user_id=user_id)

    def handle_outlook_oauth_callback(self, code: str, state: Optional[str] = None) -> Dict:
        result = handle_outlook_oauth_callback(code=code, state=state)
        if result.get("status") != "ok":
            return result

        user_id = result.get("user_id")
        if not user_id:
            return {"status": "error", "message": "Missing user_id in OAuth state"}

        tokens = result.get("tokens")
        if not isinstance(tokens, dict):
            return {"status": "error", "message": "Invalid token payload from OAuth callback"}

        ok = self._save_outlook_token(user_id, tokens)
        if not ok:
            return {"status": "error", "message": "Failed to save Outlook token"}

        return {
            "status": "ok",
            "redirect_url": result.get("redirect_url"),
            "user_id": user_id,
        }

    def get_outlook_status(self, user_id: Optional[str] = None) -> Dict:
        if not user_id:
            return {"status": "error", "authorized": False, "message": "Missing user_id"}

        try:
            outlook_client, error = self._get_outlook_client(user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Outlook not authorized"),
                }

            assert outlook_client is not None
            outlook_client.get_profile()

            return {"status": "ok", "authorized": True, "message": "Outlook authorized"}
        except Exception as exc:
            return {
                "status": "error",
                "authorized": False,
                "message": f"Error checking Outlook status: {exc}",
            }

    def get_outlook_profile(self, user_id: Optional[str] = None) -> Dict:
        if not user_id:
            return {"status": "error", "authorized": False, "message": "Missing user_id"}

        try:
            outlook_client, error = self._get_outlook_client(user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Outlook not authorized"),
                }

            assert outlook_client is not None
            profile = outlook_client.get_profile()
            token = self._get_outlook_token(user_id) or {}
            scope = token.get("scope", "")
            permissions = [s for s in str(scope).split(" ") if s]

            return {
                "status": "ok",
                "authorized": True,
                "profile": profile,
                "permissions": permissions,
            }
        except Exception as exc:
            return {"status": "error", "message": f"Error fetching Outlook profile: {exc}"}

    def revoke_outlook(self, user_id: Optional[str] = None) -> Dict:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        try:
            self.oauth_token_repository.clear_token(
                user_id=user_id,
                provider=self.PROVIDER,
                service=self.SERVICE,
            )
            return {"status": "ok", "message": "Outlook authorization removed"}
        except Exception as exc:
            return {"status": "error", "message": f"Error revoking Outlook: {exc}"}

    def list_outlook_messages(self, user_id: str, max_results: int = 20) -> Dict:
        try:
            outlook_client, error = self._get_outlook_client(user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Outlook not authorized"),
                }

            assert outlook_client is not None
            messages = outlook_client.list_messages(max_results=max_results)
            return {
                "status": "ok",
                "authorized": True,
                "messages": messages,
                "count": len(messages),
            }
        except Exception as exc:
            return {"status": "error", "message": f"Error listing Outlook messages: {exc}"}
