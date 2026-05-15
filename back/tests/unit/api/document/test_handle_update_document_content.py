"""Unit test for DocumentHandlers.handle_update_document_content."""

from src.api.document.handler import DocumentHandlers


class _DocumentContentServiceStub:
    def __init__(self):
        self.calls = []

    def update_document_content(self, document_id: str, content: str):
        self.calls.append((document_id, content))
        return {"status": "ok", "document_id": document_id}


def test_handle_update_document_content_delegates_to_service():
    handler = DocumentHandlers.__new__(DocumentHandlers)
    handler._document_content_service = _DocumentContentServiceStub()

    result = handler.handle_update_document_content("doc-1", "updated", user_id="u-1")

    assert result == {"status": "ok", "document_id": "doc-1"}
    assert handler._document_content_service.calls == [("doc-1", "updated")]
