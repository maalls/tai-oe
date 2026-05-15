"""Auth POST route dispatch for legacy API server."""

from src.api.auth.handler import (
    handle_auth_login_post,
    handle_auth_logout_post,
    handle_auth_signup_post,
)


def dispatch_post_auth_routes(handler, parsed_path: str) -> bool:
    """Dispatch auth POST routes and return True when handled."""
    if parsed_path == '/api/auth/signup':
        handle_auth_signup_post(handler)
        return True

    if parsed_path == '/api/auth/login':
        handle_auth_login_post(handler)
        return True

    if parsed_path == '/api/auth/logout':
        handle_auth_logout_post(handler)
        return True

    return False
