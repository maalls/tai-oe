"""Domain router for document endpoints."""

import re

from src.api.document.handler import (
    handle_chat_attachments_post,
    handle_document_delete,
    handle_document_extract_rfp_post,
    handle_document_update_content_post,
    handle_documents_download_get,
)


def dispatch_document_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch document routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path.startswith('/api/documents/download/'):
            handle_documents_download_get(handler, path, qs, request_handlers)
            return True
        return False

    if method == "POST":
        if path == '/api/document/extract-rfp':
            handle_document_extract_rfp_post(handler)
            return True

        if path == '/api/document/update-content':
            handle_document_update_content_post(handler)
            return True

        if path == '/api/chat/attachments':
            handle_chat_attachments_post(handler, parsed)
            return True

        return False

    if method == "DELETE":
        document_delete_match = re.match(r"^/api/document/([^/]+)$", path)
        if document_delete_match:
            handle_document_delete(handler, document_delete_match)
            return True

        return False

    return False
