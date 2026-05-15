"""Unit test for DocumentHandlers.handle_extract_rfp_from_document."""

from src.api.document.handler import DocumentHandlers


class _DocumentRfpExtractionServiceStub:
    def __init__(self):
        self.calls = []

    def extract_from_document(self, document_id: str):
        self.calls.append(document_id)
        return {"status": "ok", "document_id": document_id, "data": {"products": []}}


def test_handle_extract_rfp_from_document_delegates_to_service():
    handler = DocumentHandlers.__new__(DocumentHandlers)
    handler._document_rfp_extraction_service = _DocumentRfpExtractionServiceStub()

    result = handler.handle_extract_rfp_from_document("doc-77", user_id="u-1")

    assert result == {"status": "ok", "document_id": "doc-77", "data": {"products": []}}
    assert handler._document_rfp_extraction_service.calls == ["doc-77"]
