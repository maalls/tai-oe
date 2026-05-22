from src.service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


class _PathStub:
    def __init__(self, suffix: str, exists: bool, text: str):
        self.suffix = suffix
        self._exists = exists
        self._text = text

    def exists(self):
        return self._exists

    def read_text(self, encoding: str = "utf-8"):
        _ = encoding
        return self._text


class _DbHandlerStub:
    def __init__(self, docs):
        self.docs = docs

    def execute_dict_query(self, query, params=None):
        assert "FROM document" in query
        doc_id = params[0]
        doc = self.docs.get(doc_id)
        return [doc] if doc else []


def test_pdf_extraction_uses_vision_mode_when_enabled(monkeypatch):
    service = DocumentRfpExtractionService(
        db_handler=_DbHandlerStub({"doc-1": {"id": "doc-1", "storage_key": "doc-1.pdf"}}),
        storage_path_resolver=lambda _source, _filename: _PathStub(".pdf", True, "pdf text"),
        clean_email_body=lambda text: text,
        extract_rfp=lambda clean: {"products": [{"sku": "TEXT"}], "contact": {}},
        extract_company=lambda _clean: {},
        enrich_rfp=lambda _clean, pre: {**pre, "enriched": True},
        extract_pdf_text=lambda _path: "pdf text",
        extract_rfp_pdf_vision=lambda _path: {"products": [{"sku": "VISION"}], "contact": {}},
    )

    monkeypatch.setenv("QUOTE_EXTRACTION_MODE", "vision")
    result = service.extract_from_document("doc-1")

    assert result["status"] == "ok"
    assert result["data"]["products"][0]["sku"] == "VISION"
    assert result["data"]["enriched"] is True


def test_pdf_extraction_uses_text_mode_when_enabled(monkeypatch):
    service = DocumentRfpExtractionService(
        db_handler=_DbHandlerStub({"doc-2": {"id": "doc-2", "storage_key": "doc-2.pdf"}}),
        storage_path_resolver=lambda _source, _filename: _PathStub(".pdf", True, "pdf text"),
        clean_email_body=lambda text: f"clean:{text}",
        extract_rfp=lambda clean: {"products": [{"sku": "TEXT"}], "source": clean, "contact": {}},
        extract_company=lambda _clean: {},
        enrich_rfp=lambda _clean, pre: {**pre, "enriched": True},
        extract_pdf_text=lambda _path: "pdf text",
        extract_rfp_pdf_vision=lambda _path: {"products": [{"sku": "VISION"}], "contact": {}},
    )

    monkeypatch.setenv("QUOTE_EXTRACTION_MODE", "text")
    result = service.extract_from_document("doc-2")

    assert result["status"] == "ok"
    assert result["data"]["products"][0]["sku"] == "TEXT"
    assert result["data"]["source"] == "clean:pdf text"
    assert result["data"]["enriched"] is True
