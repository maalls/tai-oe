"""Compatibility facade for auth GET route handlers."""

from src.api.auth.handler import (
    handle_auth_user_get,
    handle_oauth_callback_get,
    handle_oauth_login_get,
)

__all__ = [
    "handle_auth_user_get",
    "handle_oauth_login_get",
    "handle_oauth_callback_get",
]
