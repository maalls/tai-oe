"""Compatibility facade for download GET route handlers."""

from src.api.document.handler import handle_document_download
from src.api.quote.handler import handle_quote_download

__all__ = [
    "handle_quote_download",
    "handle_document_download",
]
