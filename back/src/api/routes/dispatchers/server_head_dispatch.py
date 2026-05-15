"""HEAD route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.file.routes import dispatch_file_routes


def dispatch_head_request(handler, parsed_path: str) -> bool:
    """Dispatch HEAD routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers
    return dispatch_file_routes(handler, "HEAD", parsed, {}, request_handlers)
