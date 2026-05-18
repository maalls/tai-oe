"""GET route dispatch for legacy API server."""


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    return False
def dispatch_get_request(handler, parsed, qs) -> bool:
    """Dispatch GET routes and return True when handled."""
    if dispatch_get_misc_routes(handler, parsed, qs):
        return True

    return False
