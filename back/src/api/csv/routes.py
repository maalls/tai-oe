"""Domain router for CSV endpoints."""

from src.api.csv.handler import handle_csv_get, handle_csv_source_post


def dispatch_csv_routes(handler, method: str, parsed, qs) -> bool:
    """Dispatch CSV routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path.startswith('/api/csv'):
            handle_csv_get(handler, path, qs)
            return True
        return False

    if method == "POST":
        if path == '/api/csv/source':
            handle_csv_source_post(handler)
            return True
        return False

    return False
