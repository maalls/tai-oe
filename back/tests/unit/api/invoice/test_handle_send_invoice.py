"""Unit tests for InvoiceHandlers.handle_send_invoice."""

from pathlib import Path

from src.api.invoice.handler import InvoiceHandlers


class _Response:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _TableQuery:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self._op = None
        self._filters = {}
        self._payload = None

    def select(self, _fields):
        self._op = "select"
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def single(self):
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "select":
            if self._filters.get("id") == "inv-1":
                return _Response(
                    data={
                        "id": "inv-1",
                        "type": "INVOICE",
                        "external_ref": "INV-REF",
                        "opportunity_id": "opp-1",
                        "storage_key": "invoice_1.pdf",
                    }
                )
            return _Response(data=None)

        if self.table_name == "document" and self._op == "update":
            self.supabase.document_updates.append((self._filters, self._payload))
            return _Response(data=[{"id": "inv-1"}])

        if self.table_name == "sent_email" and self._op == "insert":
            self.supabase.sent_email_rows.append(self._payload)
            return _Response(data=[{"id": "se-1"}])

        return _Response(data=[])


class _SupabaseStub:
    def __init__(self):
        self.document_updates = []
        self.sent_email_rows = []

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_send_invoice_success(tmp_path):
    supabase = _SupabaseStub()
    invoice_file = tmp_path / "invoice_1.pdf"
    invoice_file.write_bytes(b"pdf")

    email_calls = []

    def _send_email_with_attachments(**kwargs):
        email_calls.append(kwargs)
        return {"status": "ok", "message_id": "msg-1"}

    handler = InvoiceHandlers(
        supabase=supabase,
        send_email_with_attachments=_send_email_with_attachments,
        storage_path_resolver=lambda source, filename: invoice_file if source == "invoice" else Path(filename),
    )

    result = handler.handle_send_invoice(
        "inv-1",
        payload={"to": ["client@example.com"], "subject": "Invoice", "body": "Body", "cc": []},
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["message"] == "Invoice sent successfully"
    assert email_calls and email_calls[0]["to"] == ["client@example.com"]
    assert supabase.document_updates
    assert supabase.sent_email_rows


def test_handle_send_invoice_requires_recipients(tmp_path):
    supabase = _SupabaseStub()
    invoice_file = tmp_path / "invoice_1.pdf"
    invoice_file.write_bytes(b"pdf")

    handler = InvoiceHandlers(
        supabase=supabase,
        send_email_with_attachments=lambda **kwargs: {"status": "ok"},
        storage_path_resolver=lambda source, filename: invoice_file,
    )

    result = handler.handle_send_invoice("inv-1", payload={"to": []}, user_id="u-1")

    assert result == {"status": "error", "message": "At least one 'to' email is required"}
