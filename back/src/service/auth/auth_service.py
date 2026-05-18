"""Authentication service for API transport layers."""

from typing import Any

from supabase import AuthApiError

from src.infrastructure.clients.supabase import get_supabase_anon


class AuthService:
    """Service wrapper around Supabase auth operations."""

    def __init__(self):
        self.supabase = get_supabase_anon()

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
            self.supabase.auth.set_session(token, token)
            self.supabase.auth.sign_out()

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
            response = self.supabase.auth.get_user(token)
            if response.user:
                return {"user": response.user.model_dump(), "status": 200}
            return {"error": "User not found", "status": 404}
        except AuthApiError as exc:
            return {"error": str(exc), "status": 401}
        except Exception as exc:
            return {"error": str(exc), "status": 500}
