import os
import requests
from urllib.parse import urlencode, urlparse

from src.infrastructure.clients.oauth.state import decode_oauth_state, encode_oauth_state


MICROSOFT_OAUTH_SCOPE = "Mail.Read Mail.Send User.Read offline_access"


def _resolve_outlook_callback_url() -> str:
    configured = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153").strip()
    parsed = urlparse(configured)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/api/outlook/oauth/callback"
    return "http://localhost:7153/api/outlook/oauth/callback"


def _oauth_settings() -> dict:
    return {
        "client_id": os.getenv("AZUR_CLIENT_ID"),
        "client_secret": os.getenv("AZUR_CLIENT_SECRET"),
        "redirect_uri": _resolve_outlook_callback_url(),
        "tenant": os.getenv("AZUR_TENANT_ID", "common"),
    }


def get_azure_oauth_url(redirect_url=None):
    """Generate Microsoft OAuth2 URL (legacy function name kept for compatibility)."""
    settings = _oauth_settings()
    client_id = settings["client_id"]
    default_redirect_uri = settings["redirect_uri"]
    tenant = settings["tenant"]

    if not client_id:
        return {
            "status": "error",
            "message": "Missing AZUR_CLIENT_ID",
        }

    state_payload = {
        "redirect_url": redirect_url or default_redirect_uri,
    }
    state = encode_oauth_state(state_payload)

    query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": default_redirect_uri,
            "response_mode": "query",
            "scope": MICROSOFT_OAUTH_SCOPE,
            "state": state,
        }
    )

    authorize_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{query}"
    return {"status": "ok", "auth_url": authorize_url}

def handle_azure_oauth_callback(code, state=None):
    """Exchange callback code for Microsoft OAuth tokens."""
    settings = _oauth_settings()
    client_id = settings["client_id"]
    client_secret = settings["client_secret"]
    redirect_uri = settings["redirect_uri"]
    tenant = settings["tenant"]

    if not client_id or not client_secret:
        return {
            "status": "error",
            "message": "Missing AZUR_CLIENT_ID or AZUR_CLIENT_SECRET",
        }

    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    redirect_url = redirect_uri
    if state:
        try:
            payload = decode_oauth_state(state)
            redirect_url = payload.get("redirect_url") or redirect_uri
        except Exception:
            pass

    data = {
        "client_id": client_id,
        "scope": MICROSOFT_OAUTH_SCOPE,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "client_secret": client_secret,
    }
    try:
        resp = requests.post(token_url, data=data, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
        return {"status": "ok", "redirect_url": redirect_url, "tokens": tokens}
    except Exception as e:
        return {"status": "error", "message": f"Microsoft OAuth failed: {e}"}
