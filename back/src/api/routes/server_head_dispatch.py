"""HEAD route dispatch for legacy API server."""

from src.api.file.handler import handle_storage_head


def dispatch_head_request(handler, parsed_path: str) -> bool:
    """Dispatch HEAD routes and return True when handled."""
    if parsed_path.startswith('/api/storage/'):
        handle_storage_head(handler, handler.config['STORAGE_DIR'], parsed_path)
        return True

    return False
