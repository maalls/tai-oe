"""Tests for InvoiceService.handle_generate_invoice_from_quote."""

from service.invoice.invoice_service import InvoiceService


class _DbHandler:
    def __init__(self):
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "FROM document WHERE id" in query:
            return []
        if "WHERE opportunity_id = %s" in query and "type = 'QUOTE'" in query:
            return [
                {
                    "id": "q-1",
                    "type": "QUOTE",
                    "opportunity_id": "opp-1",
                    "title": "Quote Alpha",
                    "currency": "EUR",
                    "total_excl_tax": 100,
                    "total_tax": 20,
                    "total_incl_tax": 120,
                }
            ]
        if "parent_document_id" in query and "type = 'INVOICE'" in query:
            return []
        if "FROM document_line" in query:
            return [
                {
                    "position": 1,
                    "sku": "SKU-1",
                    "brand": "ACME",
                    "description": "Item",
                    "quantity": 2,
                    "unit": "U",
                    "unit_price_excl_tax": 50,
                    "tax_rate": 20,
                    "line_total_excl_tax": 100,
                }
            ]
        if "INSERT INTO document" in query:
            return [{"id": "inv-1"}]
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_handle_generate_invoice_from_quote_creates_invoice_and_lines(monkeypatch):
    db_handler = _DbHandler()
    service = InvoiceService(db_handler=db_handler)

    monkeypatch.setattr(
        service,
        "handle_generate_invoice_pdf",
        lambda document_id, user_id=None: {"status": "ok", "storage_key": "invoice_1.pdf"},
    )

    result = service.handle_generate_invoice_from_quote("opp-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["invoice_id"] == "inv-1"
    assert result["invoice"]["storage_key"] == "invoice_1.pdf"
    assert len(db_handler.update_calls) == 1
    assert "INSERT INTO document_line" in db_handler.update_calls[0][0]


def test_handle_generate_invoice_from_quote_returns_error_when_quote_missing():
    class _MissingQuoteDbHandler(_DbHandler):
        def execute_dict_query(self, query, params=None):
            if "FROM document WHERE id" in query:
                return []
            if "WHERE opportunity_id = %s" in query and "type = 'QUOTE'" in query:
                return []
            return super().execute_dict_query(query, params)

    service = InvoiceService(db_handler=_MissingQuoteDbHandler())

    result = service.handle_generate_invoice_from_quote("missing")

    assert result["status"] == "error"
    assert "Quote not found" in result["message"]
