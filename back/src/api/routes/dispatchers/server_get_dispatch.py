"""GET route dispatch for legacy API server."""

from src.api.csv.routes import dispatch_csv_routes


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    return False


def dispatch_get_data_routes(handler, parsed, qs) -> bool:
    """Dispatch csv GET routes and return True when handled."""
    if dispatch_csv_routes(handler, "GET", parsed, qs):
        return True

    return False


def dispatch_get_request(handler, parsed, qs) -> bool:
    """Dispatch GET routes and return True when handled."""
    if dispatch_get_misc_routes(handler, parsed, qs):
        return True

    if dispatch_get_data_routes(handler, parsed, qs):
        return True

    return False
