"""Tests for DocumentService.handle_chat_attachment_upload."""

from service.document.document_service import DocumentService


class _DirStub:
    def __init__(self):
        self.mkdir_calls = []
        self.files = {}

    def mkdir(self, parents=False, exist_ok=False):
        self.mkdir_calls.append((parents, exist_ok))

    def __truediv__(self, key):
        return _FileStub(self.files, key)


class _FileStub:
    def __init__(self, files, key):
        self.files = files
        self.key = key

    def write_bytes(self, content):
        self.files[self.key] = content


class _DbHandler:
    def __init__(self):
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "INSERT INTO document" in query:
            return [{"id": "doc-1"}]
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_handle_chat_attachment_upload_creates_document_and_touches_opportunity(monkeypatch):
    dir_stub = _DirStub()
    db_handler = _DbHandler()
    service = DocumentService(
        db_handler=db_handler,
        storage_dir_resolver=lambda _source: dir_stub,
    )

    monkeypatch.setattr("service.document.document_service.time.time", lambda: 123)
    monkeypatch.setattr(
        "service.document.document_service.uuid.uuid4",
        lambda: type("U", (), {"hex": "abc123"})(),
    )

    result = service.handle_chat_attachment_upload(
        filename="spec.pdf",
        file_content=b"pdf",
        mime_type="application/pdf",
        file_size=3,
        user_id="u-1",
        opportunity_id="opp-1",
    )

    assert result["status"] == "ok"
    assert result["document_id"] == "doc-1"
    assert result["storage_key"] == "123_abc123_spec.pdf"
    assert dir_stub.files["123_abc123_spec.pdf"] == b"pdf"
    assert any("UPDATE opportunity SET updated_at" in call[0] for call in db_handler.update_calls)


def test_handle_chat_attachment_upload_validates_required_fields():
    service = DocumentService(db_handler=_DbHandler(), storage_dir_resolver=lambda _source: _DirStub())

    assert service.handle_chat_attachment_upload("f", b"x", "m", 1, user_id="", opportunity_id="opp")["status"] == "error"
    assert service.handle_chat_attachment_upload("f", b"x", "m", 1, user_id="u", opportunity_id="")["status"] == "error"
    assert service.handle_chat_attachment_upload("", b"", "m", 0, user_id="u", opportunity_id="opp")["status"] == "error"
