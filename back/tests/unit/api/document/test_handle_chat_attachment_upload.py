"""Unit tests for DocumentHandlers.handle_chat_attachment_upload."""

from pathlib import Path

from src.api.document.handler import DocumentHandlers


class _Response:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _TableQuery:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self._op = None
        self._payload = None

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "insert":
            self.supabase.inserted_doc = self._payload
            return _Response(data=[{"id": "doc-1"}])
        if self.table_name == "opportunity" and self._op == "update":
            return _Response(data=[{"id": "opp-1"}])
        return _Response(data=[])


class _SupabaseStub:
    def __init__(self):
        self.inserted_doc = None

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_chat_attachment_upload_success(tmp_path):
    storage_dir = tmp_path / "attachments"
    supabase = _SupabaseStub()

    handler = DocumentHandlers(
        supabase=supabase,
        storage_dir_resolver=lambda source: storage_dir,
    )

    body = (
        b"--x\r\n"
        b"Content-Disposition: form-data; name=\"file\"; filename=\"a.txt\"\r\n"
        b"Content-Type: text/plain\r\n\r\n"
        b"hello\r\n"
        b"--x--\r\n"
    )

    result = handler.handle_chat_attachment_upload(
        body=body,
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
        opportunity_id="opp-1",
    )

    assert result["status"] == "ok"
    assert result["document_id"] == "doc-1"
    assert supabase.inserted_doc is not None
    stored_files = list(storage_dir.glob("*a.txt"))
    assert len(stored_files) == 1


def test_handle_chat_attachment_upload_requires_user_and_opportunity():
    handler = DocumentHandlers(supabase=_SupabaseStub(), storage_dir_resolver=lambda source: Path("."))

    result_missing_user = handler.handle_chat_attachment_upload(
        body=b"",
        content_type="multipart/form-data; boundary=x",
        user_id="",
        opportunity_id="opp-1",
    )
    result_missing_opp = handler.handle_chat_attachment_upload(
        body=b"",
        content_type="multipart/form-data; boundary=x",
        user_id="u-1",
        opportunity_id="",
    )

    assert result_missing_user == {"status": "error", "message": "Missing user_id"}
    assert result_missing_opp == {"status": "error", "message": "Missing opportunity_id"}
