"""Domain router for file/storage endpoints."""

from src.api.file.handler import (
    handle_storage_get,
    handle_storage_head,
)


def dispatch_file_routes(handler, method: str, parsed, qs, _request_handlers) -> bool:
    """Dispatch file/storage routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path.startswith('/api/storage/'):
            handle_storage_get(handler, handler.config['STORAGE_DIR'], path)
            return True

        return False

    if method == "HEAD":
        if path.startswith('/api/storage/'):
            handle_storage_head(handler, handler.config['STORAGE_DIR'], path)
            return True

        return False

    if method == "POST":
        return False

    return False
