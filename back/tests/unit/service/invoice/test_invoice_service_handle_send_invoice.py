"""Tests for InvoiceService.handle_send_invoice."""

from pathlib import Path

from service.invoice.invoice_service import InvoiceService


class _DbHandler:
    def __init__(self, storage_key="invoice.pdf"):
        self.storage_key = storage_key
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "FROM document WHERE id" in query:
            return [
                {
                    "id": "inv-1",
                    "type": "INVOICE",
                    "opportunity_id": "opp-1",
                    "external_ref": "INV-001",
                    "storage_key": self.storage_key,
                }
            ]
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_handle_send_invoice_sends_and_persists(tmp_path):
    pdf_path = tmp_path / "invoice.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    sent_payload = {}

    def _send_email_with_attachments(**kwargs):
        sent_payload.update(kwargs)
        return {"status": "ok", "message_id": "m-1"}

    service = InvoiceService(
        db_handler=_DbHandler(storage_key="invoice.pdf"),
        send_email_with_attachments=_send_email_with_attachments,
        storage_path_resolver=lambda source, key: pdf_path,
    )

    result = service.handle_send_invoice(
        "inv-1",
        payload={"to": ["buyer@example.com"], "subject": "Invoice", "body": "Hi"},
        user_id="u-1",
    )

    assert result["status"] == "ok"
    assert result["message_id"] == "m-1"
    assert sent_payload["to"] == ["buyer@example.com"]


def test_handle_send_invoice_requires_recipient_list(tmp_path):
    pdf_path = tmp_path / "invoice.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    service = InvoiceService(
        db_handler=_DbHandler(storage_key="invoice.pdf"),
        send_email_with_attachments=lambda **kwargs: {"status": "ok", "message_id": "m-1"},
        storage_path_resolver=lambda source, key: Path(pdf_path),
    )

    result = service.handle_send_invoice("inv-1", payload={"to": []})

    assert result["status"] == "error"
    assert "At least one 'to' email" in result["message"]
