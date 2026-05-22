"""Microsoft Graph Outlook client and OAuth helpers."""

import time
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse
import os

import requests

from src.infrastructure.clients.oauth.state import decode_oauth_state, encode_oauth_state


MICROSOFT_OAUTH_SCOPE = "Mail.Read Mail.Send User.Read offline_access"


def _resolve_outlook_callback_url() -> str:
    configured = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153").strip()
    parsed = urlparse(configured)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/api/outlook/oauth/callback"
    return "http://localhost:7153/api/outlook/oauth/callback"


def _oauth_settings() -> dict[str, str]:
    return {
        "client_id": os.getenv("AZUR_CLIENT_ID", ""),
        "client_secret": os.getenv("AZUR_CLIENT_SECRET", ""),
        "redirect_uri": _resolve_outlook_callback_url(),
        "tenant": os.getenv("AZUR_TENANT_ID", "common"),
    }


def get_outlook_oauth_url(redirect_url: Optional[str] = None, user_id: Optional[str] = None) -> dict[str, Any]:
    settings = _oauth_settings()
    client_id = settings["client_id"]
    callback_url = settings["redirect_uri"]
    tenant = settings["tenant"]

    if not client_id:
        return {
            "status": "error",
            "message": "Missing AZUR_CLIENT_ID",
        }

    state = encode_oauth_state(
        {
            "redirect_url": redirect_url or callback_url,
            "user_id": user_id,
        }
    )

    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": callback_url,
            "response_mode": "query",
            "scope": MICROSOFT_OAUTH_SCOPE,
            "state": state,
        }
    )

    auth_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{query}"
    return {"status": "ok", "auth_url": auth_url}


def handle_outlook_oauth_callback(code: str, state: Optional[str] = None) -> dict[str, Any]:
    settings = _oauth_settings()
    client_id = settings["client_id"]
    client_secret = settings["client_secret"]
    callback_url = settings["redirect_uri"]
    tenant = settings["tenant"]

    if not client_id or not client_secret:
        return {
            "status": "error",
            "message": "Missing AZUR_CLIENT_ID or AZUR_CLIENT_SECRET",
        }

    redirect_url = callback_url
    user_id = None
    if state:
        payload = decode_oauth_state(state)
        redirect_url = payload.get("redirect_url") or callback_url
        user_id = payload.get("user_id")

    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": callback_url,
        "grant_type": "authorization_code",
        "scope": MICROSOFT_OAUTH_SCOPE,
    }

    try:
        response = requests.post(token_url, data=data, timeout=15)
        response.raise_for_status()
        raw_tokens = response.json()
        expires_in = int(raw_tokens.get("expires_in", 3600))
        token_dict = {
            "access_token": raw_tokens.get("access_token", ""),
            "refresh_token": raw_tokens.get("refresh_token", ""),
            "token_type": raw_tokens.get("token_type", "Bearer"),
            "scope": raw_tokens.get("scope", MICROSOFT_OAUTH_SCOPE),
            "expires_at": int(time.time()) + max(expires_in - 60, 0),
        }
        return {
            "status": "ok",
            "tokens": token_dict,
            "user_id": user_id,
            "redirect_url": redirect_url,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Microsoft OAuth failed: {exc}",
        }


class OutlookClient:
    """Minimal Microsoft Graph client for profile and message access."""

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: int,
        client_id: str,
        client_secret: str,
        tenant: str,
        token_saver: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token or ""
        self.expires_at = int(expires_at or 0)
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant or "common"
        self.token_saver = token_saver

    def _refresh_if_needed(self) -> None:
        now = int(time.time())
        if self.expires_at > now + 30:
            return

        if not self.refresh_token:
            raise PermissionError("OUTLOOK_NOT_AUTHORIZED: Missing refresh token")

        token_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": MICROSOFT_OAUTH_SCOPE,
        }

        response = requests.post(token_url, data=data, timeout=15)
        response.raise_for_status()
        refreshed = response.json()

        self.access_token = refreshed.get("access_token", self.access_token)
        self.refresh_token = refreshed.get("refresh_token", self.refresh_token)
        expires_in = int(refreshed.get("expires_in", 3600))
        self.expires_at = int(time.time()) + max(expires_in - 60, 0)

        if self.token_saver:
            self.token_saver(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at,
                    "token_type": refreshed.get("token_type", "Bearer"),
                    "scope": refreshed.get("scope", MICROSOFT_OAUTH_SCOPE),
                }
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_profile(self) -> dict[str, Any]:
        self._refresh_if_needed()
        response = requests.get("https://graph.microsoft.com/v1.0/me", headers=self._headers(), timeout=15)
        response.raise_for_status()
        return response.json()

    def list_messages(self, max_results: int = 20) -> list[dict[str, Any]]:
        self._refresh_if_needed()
        url = (
            "https://graph.microsoft.com/v1.0/me/messages"
            f"?$top={max_results}&$select=id,subject,from,receivedDateTime,bodyPreview"
        )
        response = requests.get(url, headers=self._headers(), timeout=15)
        response.raise_for_status()
        payload = response.json()
        return payload.get("value", [])

    def send_message(self, to: str, subject: str, body: str) -> dict[str, Any]:
        self._refresh_if_needed()
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to,
                        }
                    }
                ],
            },
            "saveToSentItems": True,
        }
        response = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return {"status": "ok"}
