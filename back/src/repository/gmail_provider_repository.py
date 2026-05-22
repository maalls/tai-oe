"""Gmail provider repository for OAuth/profile operations."""

import base64
import os
import pickle
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from google_auth_oauthlib.flow import Flow

from src.infrastructure.clients.gmail_client import GmailClient
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.supabase.email_database_handler import EmailDatabaseHandler
from src.infrastructure.clients.oauth.state import decode_oauth_state, encode_oauth_state


def _resolve_frontend_redirect_url(default_path: str = "/settings") -> str:
    configured = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153").strip()
    parsed = urlparse(configured)

    if not parsed.scheme or not parsed.netloc:
        return f"http://localhost:7153{default_path}"

    path = parsed.path.rstrip("/")
    if path:
        return configured.rstrip("/")

    return f"{parsed.scheme}://{parsed.netloc}{default_path}"


class GmailProviderRepository:
    """Repository dedicated to Gmail OAuth and profile interactions."""

    def __init__(
        self,
        db_handler: Optional[DatabaseHandler] = None,
        email_db_handler: Optional[EmailDatabaseHandler] = None,
    ):
        self.email_db_handler = email_db_handler or EmailDatabaseHandler(db_handler=db_handler)

    def _resolve_gmail_callback_url(self, redirect_url: Optional[str]) -> str:
        default_origin = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153")
        candidate = redirect_url or default_origin
        parsed = urlparse(candidate)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/api/gmail/oauth/callback"

        return "http://localhost:7153/api/gmail/oauth/callback"

    @staticmethod
    def _get_gmail_paths() -> tuple:
        var_dir = Path(__file__).parent.parent.parent / "var"
        credentials_path = var_dir / "credentials.json"
        token_path = var_dir / "token.pickle"
        return credentials_path, token_path

    def _get_profile_column(self, user_id: str, column: str) -> Optional[str]:
        try:
            return self.email_db_handler.get_profile_column(user_id, column)
        except Exception as exc:
            print(f"[GmailProviderRepository] Error reading profile column '{column}': {exc}")
        return None

    def _set_profile_column(self, user_id: str, column: str, value: Optional[str]) -> bool:
        try:
            return self.email_db_handler.set_profile_column(user_id, column, value)
        except Exception as exc:
            print(f"[GmailProviderRepository] Error setting profile column '{column}': {exc}")
            return False

    def _get_profile_token_b64(self, user_id: str) -> Optional[str]:
        return self._get_profile_column(user_id, "google_token_pickle")

    def _save_profile_token(self, user_id: str, creds) -> bool:
        try:
            token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
            return self._set_profile_column(user_id, "google_token_pickle", token_b64)
        except Exception as exc:
            print(f"[GmailProviderRepository] Error saving profile token: {exc}")
            return False

    def _clear_profile_token(self, user_id: str) -> bool:
        return self._set_profile_column(user_id, "google_token_pickle", None)

    def _get_gmail_client(self, user_id: str = None) -> tuple:
        credentials_path, token_path = self._get_gmail_paths()

        if not credentials_path.exists():
            return None, {
                "status": "error",
                "error_code": "GMAIL_NOT_CONFIGURED",
                "message": "Gmail credentials not configured",
            }

        token_bytes = None
        token_saver = None

        if user_id:
            token_b64 = self._get_profile_token_b64(user_id)
            if token_b64:
                try:
                    token_bytes = base64.b64decode(token_b64.encode("utf-8"))
                    token_saver = lambda creds: self._save_profile_token(user_id, creds)
                except Exception:
                    token_bytes = None

        if not token_bytes and not token_path.exists():
            return None, {
                "status": "error",
                "error_code": "GMAIL_NOT_AUTHORIZED",
                "message": "Gmail not authorized. Please authorize first.",
            }

        gmail_client = GmailClient(
            credentials_path=str(credentials_path),
            token_path=str(token_path),
            token_bytes=token_bytes,
            token_saver=token_saver,
        )
        return gmail_client, None

    def authorize_gmail(self, redirect_url: str = None) -> Dict:
        try:
            credentials_path, token_path = self._get_gmail_paths()

            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json",
                }

            if not redirect_url:
                redirect_url = _resolve_frontend_redirect_url()

            callback_url = self._resolve_gmail_callback_url(redirect_url)

            try:
                gmail_client = GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(token_path),
                    redirect_url=callback_url,
                )
                gmail_client.get_service()
                return {
                    "status": "ok",
                    "message": "Gmail authorization successful",
                }
            except Exception as exc:
                return {
                    "status": "error",
                    "message": f"Authorization failed: {exc}",
                }

        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error during authorization: {exc}",
            }

    def get_gmail_oauth_url(self, redirect_url: str = None, user_id: str = None) -> Dict:
        try:
            credentials_path, _ = self._get_gmail_paths()

            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json",
                }

            if not user_id:
                return {"status": "error", "message": "Missing user_id"}

            resolved_redirect_url = redirect_url or _resolve_frontend_redirect_url()
            callback_url = self._resolve_gmail_callback_url(resolved_redirect_url)
            flow = Flow.from_client_secrets_file(
                str(credentials_path),
                scopes=GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(self._get_gmail_paths()[1]),
                ).scopes,
                redirect_uri=callback_url,
            )

            state = encode_oauth_state(
                {
                    "redirect_url": resolved_redirect_url,
                    "callback_url": callback_url,
                    "user_id": user_id,
                }
            )

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
                state=state,
            )

            return {"status": "ok", "auth_url": auth_url}
        except Exception as exc:
            return {"status": "error", "message": f"Error starting Gmail OAuth: {exc}"}

    def handle_gmail_oauth_callback(self, code: str, state: str = None) -> Dict:
        try:
            credentials_path, token_path = self._get_gmail_paths()

            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json",
                }

            redirect_url = _resolve_frontend_redirect_url()
            callback_url = self._resolve_gmail_callback_url(redirect_url)
            user_id = None
            if state:
                payload = decode_oauth_state(state)
                redirect_url = payload.get("redirect_url") or redirect_url
                callback_url = payload.get("callback_url") or self._resolve_gmail_callback_url(redirect_url)
                user_id = payload.get("user_id")

            flow = Flow.from_client_secrets_file(
                str(credentials_path),
                scopes=GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(token_path),
                ).scopes,
                redirect_uri=callback_url,
            )

            flow.fetch_token(code=code)
            creds = flow.credentials

            if user_id:
                self._save_profile_token(user_id, creds)
            else:
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

            return {"status": "ok", "redirect_url": redirect_url}
        except Exception as exc:
            return {"status": "error", "message": f"Error handling Gmail OAuth callback: {exc}"}

    def get_gmail_status(self, user_id: str = None) -> Dict:
        try:
            gmail_client, error = self._get_gmail_client(user_id=user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Gmail not authorized"),
                }

            try:
                gmail_client.get_service()
            except PermissionError as exc:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": "GMAIL_NOT_AUTHORIZED",
                    "message": str(exc),
                }

            return {"status": "ok", "authorized": True, "message": "Gmail authorized"}
        except Exception as exc:
            return {
                "status": "error",
                "authorized": False,
                "message": f"Error checking Gmail status: {exc}",
            }

    def revoke_gmail(self, user_id: str = None) -> Dict:
        try:
            if user_id:
                self._clear_profile_token(user_id)
            else:
                _, token_path = self._get_gmail_paths()
                if token_path.exists():
                    token_path.unlink()
            return {"status": "ok", "message": "Gmail authorization removed"}
        except Exception as exc:
            return {"status": "error", "message": f"Error revoking Gmail: {exc}"}

    def get_gmail_profile(self, user_id: str = None) -> Dict:
        try:
            gmail_client, error = self._get_gmail_client(user_id=user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Gmail not authorized"),
                }

            try:
                service = gmail_client.get_service()
            except PermissionError as exc:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": "GMAIL_NOT_AUTHORIZED",
                    "message": str(exc),
                }

            profile = service.users().getProfile(userId="me").execute()

            scopes = []
            if user_id:
                token_b64 = self._get_profile_token_b64(user_id)
                if token_b64:
                    try:
                        creds = pickle.loads(base64.b64decode(token_b64.encode("utf-8")))
                        scopes = list(getattr(creds, "scopes", []) or [])
                    except Exception:
                        scopes = []
            else:
                _, token_path = self._get_gmail_paths()
                if token_path.exists():
                    try:
                        with open(token_path, "rb") as token:
                            creds = pickle.load(token)
                            scopes = list(getattr(creds, "scopes", []) or [])
                    except Exception:
                        scopes = []

            if not scopes:
                scopes = list(getattr(gmail_client, "scopes", []) or [])

            return {
                "status": "ok",
                "authorized": True,
                "profile": profile,
                "permissions": scopes,
            }
        except Exception as exc:
            return {"status": "error", "message": f"Error fetching Gmail profile: {exc}"}
