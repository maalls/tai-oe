"""Auth/OAuth GET route dispatch for legacy API server."""

from src.api.auth.handler import handle_auth_user_get, handle_oauth_callback_get, handle_oauth_login_get


def dispatch_get_auth_routes(handler, parsed, qs) -> bool:
    """Dispatch auth GET routes and return True when handled."""
    if parsed.path == '/api/auth/user':
        handle_auth_user_get(handler)
        return True

    if parsed.path == '/api/oauth/login':
        handle_oauth_login_get(handler, qs)
        return True

    if parsed.path == '/api/oauth/callback':
        handle_oauth_callback_get(handler, qs)
        return True

    return False
