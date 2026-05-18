"""HEAD route dispatch for legacy API server."""

def dispatch_head_request(handler, parsed_path: str) -> bool:
    """Dispatch HEAD routes and return True when handled."""
    _ = (handler, parsed_path)
    return False
