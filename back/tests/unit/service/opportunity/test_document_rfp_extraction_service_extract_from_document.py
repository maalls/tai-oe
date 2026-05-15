"""Tests for DocumentRfpExtractionService.extract_from_document."""

from service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


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


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, db):
        self.db = db
        self.doc_id = None

    def select(self, _fields):
        return self

    def eq(self, field, value):
        assert field == "id"
        self.doc_id = value
        return self

    def single(self):
        return self

    def execute(self):
        return _Response(self.db.docs.get(self.doc_id))


class _SupabaseStub:
    def __init__(self, docs):
        self.docs = docs

    def table(self, table_name: str):
        assert table_name == "document"
        return _Query(self)


def test_extract_from_document_success_for_text_file():
    supabase = _SupabaseStub(
        {
            "doc-1": {
                "id": "doc-1",
                "storage_key": "doc-1.txt",
            }
        }
    )

    service = DocumentRfpExtractionService(
        supabase=supabase,
        storage_path_resolver=lambda _source, _filename: _PathStub(".txt", True, "raw content"),
        clean_email_body=lambda text: f"clean:{text}",
        extract_rfp=lambda clean: {"products": [{"sku": "A1"}], "contact": {}, "source": clean},
        extract_company=lambda _clean: {"company": "ACME"},
        enrich_rfp=lambda _clean, pre: {**pre, "enriched": True},
    )

    result = service.extract_from_document("doc-1")

    assert result["status"] == "ok"
    assert result["document_id"] == "doc-1"
    assert result["data"]["enriched"] is True
    assert result["data"]["contact"] == {"company": "ACME"}


def test_extract_from_document_returns_error_when_document_missing():
    service = DocumentRfpExtractionService(
        supabase=_SupabaseStub({}),
        storage_path_resolver=lambda _source, _filename: _PathStub(".txt", False, ""),
        clean_email_body=lambda text: text,
        extract_rfp=lambda clean: {},
        extract_company=lambda clean: {},
        enrich_rfp=lambda clean, pre: pre,
    )

    result = service.extract_from_document("missing")

    assert result == {"status": "error", "message": "Document not found"}
