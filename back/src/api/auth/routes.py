"""Domain router for auth endpoints."""

from src.api.auth.handler import (
    handle_auth_login_post,
    handle_auth_logout_post,
    handle_auth_signup_post,
    handle_auth_user_get,
    handle_oauth_callback_get,
    handle_oauth_login_get,
)


def dispatch_auth_routes(handler, method: str, parsed, qs) -> bool:
    """Dispatch auth routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path == '/api/auth/user':
            handle_auth_user_get(handler)
            return True

        if path == '/api/oauth/login':
            handle_oauth_login_get(handler, qs)
            return True

        if path == '/api/oauth/callback':
            handle_oauth_callback_get(handler, qs)
            return True

        return False

    if method == "POST":
        if path == '/api/auth/signup':
            handle_auth_signup_post(handler)
            return True

        if path == '/api/auth/login':
            handle_auth_login_post(handler)
            return True

        if path == '/api/auth/logout':
            handle_auth_logout_post(handler)
            return True

        return False

    return False
