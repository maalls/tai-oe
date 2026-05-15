"""Auth POST route dispatch for legacy API server."""


def dispatch_post_auth_routes(handler, parsed_path: str) -> bool:
    """Dispatch auth POST routes and return True when handled."""
    if parsed_path == '/api/auth/signup':
        handler._handle_auth_signup_post()
        return True

    if parsed_path == '/api/auth/login':
        handler._handle_auth_login_post()
        return True

    if parsed_path == '/api/auth/logout':
        handler._handle_auth_logout_post()
        return True

    return False
