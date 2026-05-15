"""HTTP status mapping helpers for legacy API server."""


def status_from_result(result: dict, ok: int = 200, error: int = 400) -> int:
    """Map handler result payload status to HTTP status code."""
    return ok if result.get('status') == 'ok' else error


def pop_status(result: dict, default: int = 200) -> int:
    """Extract and remove status code from handler payload."""
    return result.pop('status', default)


def status_from_error(result: dict, ok: int = 200, error: int = 400, key: str = 'error') -> int:
    """Map payload error field presence to HTTP status code."""
    return error if result.get(key) else ok
