"""Authentication service for API transport layers."""

from typing import Any

import requests
from supabase import AuthApiError

from src.infrastructure.clients.supabase import _resolve_supabase_credentials, get_supabase_anon


class AuthService:
    """Service wrapper around Supabase auth operations."""

    def __init__(self):
        self.supabase = get_supabase_anon()

    @staticmethod
    def _resolve_auth_endpoint() -> tuple[str, str]:
        supabase_url, supabase_anon_key, _ = _resolve_supabase_credentials()
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured")
        return supabase_url.rstrip("/"), supabase_anon_key

    def _fetch_user_from_token(self, token: str) -> dict[str, Any] | None:
        supabase_url, supabase_anon_key = self._resolve_auth_endpoint()
        response = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": supabase_anon_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=20,
        )
        if response.status_code != 200:
            return None

        payload = response.json()
        if isinstance(payload, dict) and payload.get("id"):
            return payload
        return None

    def signup(self, email: str, password: str) -> dict[str, Any]:
        try:
            if not email or not password:
                return {"error": "Email and password are required", "status": 400}

            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
            })

            return {
                "user": response.user.model_dump() if response.user else None,
                "session": response.session.model_dump() if response.session else None,
                "status": 201,
            }
        except AuthApiError as exc:
            return {"error": str(exc), "status": 400}
        except Exception as exc:
            return {"error": str(exc), "status": 500}

    def login(self, email: str, password: str) -> dict[str, Any]:
        try:
            if not email or not password:
                return {"error": "Email and password are required", "status": 400}

            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            return {
                "user": response.user.model_dump() if response.user else None,
                "session": response.session.model_dump() if response.session else None,
                "access_token": response.session.access_token if response.session else None,
                "status": 200,
            }
        except AuthApiError as exc:
            return {"error": str(exc), "status": 401}
        except Exception as exc:
            return {"error": str(exc), "status": 500}

    def logout(self, auth_header: str) -> dict[str, Any]:
        try:
            if not auth_header or not auth_header.startswith("Bearer "):
                return {"error": "No authorization token provided", "status": 401}

            token = auth_header.split(" ", 1)[1]
            supabase_url, supabase_anon_key = self._resolve_auth_endpoint()
            response = requests.post(
                f"{supabase_url}/auth/v1/logout",
                headers={
                    "apikey": supabase_anon_key,
                    "Authorization": f"Bearer {token}",
                },
                timeout=20,
            )
            if response.status_code not in (200, 204):
                return {"error": response.text or "Logout failed", "status": 401}

            return {"message": "Logged out successfully", "status": 200}
        except AuthApiError as exc:
            return {"error": str(exc), "status": 401}
        except Exception as exc:
            return {"error": str(exc), "status": 500}

    def get_user(self, auth_header: str) -> dict[str, Any]:
        try:
            if not auth_header or not auth_header.startswith("Bearer "):
                return {"error": "No authorization token provided", "status": 401}

            token = auth_header.split(" ", 1)[1]
            user = self._fetch_user_from_token(token)
            if user:
                return {"user": user, "status": 200}
            return {"error": "Invalid authentication credentials", "status": 401}
        except AuthApiError as exc:
            return {"error": str(exc), "status": 401}
        except Exception as exc:
            return {"error": str(exc), "status": 500}

    def verify_token(self, auth_header: str) -> tuple[bool, dict[str, Any] | None]:
        try:
            if not auth_header or not auth_header.startswith("Bearer "):
                return False, None

            token = auth_header.split(" ", 1)[1]
            user = self._fetch_user_from_token(token)
            if user:
                return True, user
            return False, None
        except Exception:
            return False, None
