"""Tests for InvoiceService.handle_generate_invoice_pdf."""

from service.invoice.invoice_service import InvoiceService


class _DbHandler:
    def __init__(self):
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "FROM document WHERE id" in query:
            return [
                {
                    "id": "inv-1",
                    "type": "INVOICE",
                    "opportunity_id": "opp-1",
                    "external_ref": "INV-001",
                    "title": "Invoice Alpha",
                    "issued_at": "2026-05-22T10:00:00",
                    "currency": "EUR",
                    "total_excl_tax": 100,
                    "total_tax": 20,
                    "total_incl_tax": 120,
                }
            ]
        if "FROM opportunity" in query:
            return [{"id": "opp-1", "account_id": "acc-1"}]
        if "FROM account" in query:
            return [{"id": "acc-1", "name": "Acme"}]
        if "FROM document_line" in query:
            return [
                {
                    "quantity": 2,
                    "brand": "ACME",
                    "sku": "SKU-1",
                    "description": "Item",
                    "unit_price_excl_tax": 50,
                    "tax_rate": 20,
                    "unit": "U",
                }
            ]
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_handle_generate_invoice_pdf_updates_storage_key(monkeypatch):
    db_handler = _DbHandler()
    service = InvoiceService(db_handler=db_handler)

    monkeypatch.setattr(service, "_generate_invoice_pdf", lambda _invoice_data: "invoice_generated.pdf")

    result = service.handle_generate_invoice_pdf("inv-1", user_id="u-1")

    assert result == {"status": "ok", "storage_key": "invoice_generated.pdf"}
    assert len(db_handler.update_calls) == 1
    assert db_handler.update_calls[0][1] == ("invoice_generated.pdf", "inv-1")


def test_handle_generate_invoice_pdf_rejects_non_invoice_type():
    class _WrongTypeDbHandler(_DbHandler):
        def execute_dict_query(self, query, params=None):
            if "FROM document WHERE id" in query:
                return [{"id": "doc-1", "type": "QUOTE"}]
            return super().execute_dict_query(query, params)

    service = InvoiceService(db_handler=_WrongTypeDbHandler())

    result = service.handle_generate_invoice_pdf("doc-1")

    assert result["status"] == "error"
    assert "only supported for invoices" in result["message"]
