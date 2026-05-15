"""Compatibility facade for misc GET route handlers."""

from src.api.email.handler import handle_google_oauth_callback_get
from src.api.file.handler import handle_fetch_get, handle_prompt_get
from src.api.product.handler import handle_products_get


def handle_email_fetch_loop_status_get(handler, current_file: str):
    """Handle /api/email-fetch-loop/status GET endpoint."""
    from pathlib import Path

    status_path = Path(current_file).resolve().parents[3] / 'var' / 'email_fetch_loop.json'
    legacy_path = Path(current_file).resolve().parents[2] / 'var' / 'email_fetch_loop.json'
    request_handlers = handler.request_handlers
    result = request_handlers.handle_email_fetch_loop_status(status_path=status_path, legacy_path=legacy_path)
    return handler.json(result)


__all__ = [
    "handle_products_get",
    "handle_google_oauth_callback_get",
    "handle_email_fetch_loop_status_get",
    "handle_fetch_get",
    "handle_prompt_get",
]
