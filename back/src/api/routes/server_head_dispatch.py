"""HEAD route dispatch for legacy API server."""


def dispatch_head_request(handler, parsed_path: str) -> bool:
    """Dispatch HEAD routes and return True when handled."""
    if parsed_path.startswith('/api/storage/'):
        handler._handle_storage_head(parsed_path)
        return True

    return False
