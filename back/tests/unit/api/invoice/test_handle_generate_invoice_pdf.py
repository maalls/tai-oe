"""Unit tests for InvoiceHandlers.handle_generate_invoice_pdf."""

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

    def order(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "select":
            if self._filters.get("id") == "inv-1":
                return _Response(
                    data={
                        "id": "inv-1",
                        "type": "INVOICE",
                        "opportunity_id": "opp-1",
                        "external_ref": "INV-123",
                        "title": "Invoice 123",
                        "issued_at": "2026-01-01T00:00:00",
                        "currency": "EUR",
                        "total_excl_tax": 100,
                        "total_tax": 20,
                        "total_incl_tax": 120,
                    }
                )
            return _Response(data=None)

        if self.table_name == "opportunity" and self._op == "select":
            return _Response(data={"id": "opp-1", "account_id": "acc-1"})

        if self.table_name == "account" and self._op == "select":
            return _Response(data={"id": "acc-1", "name": "Acme", "city": "Paris"})

        if self.table_name == "document_line" and self._op == "select":
            return _Response(
                data=[
                    {
                        "quantity": 2,
                        "brand": "Brand",
                        "sku": "SKU-1",
                        "description": "Desc",
                        "unit_price_excl_tax": 50,
                        "tax_rate": 20,
                        "unit": "U",
                    }
                ]
            )

        if self.table_name == "document" and self._op == "update":
            self.supabase.updated_document_payload = self._payload
            return _Response(data=[{"id": "inv-1"}])

        return _Response(data=[])


class _SupabaseStub:
    def __init__(self):
        self.updated_document_payload = None

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_generate_invoice_pdf_success(monkeypatch):
    supabase = _SupabaseStub()
    handler = InvoiceHandlers(supabase=supabase)

    monkeypatch.setattr(handler, "_generate_invoice_pdf", lambda invoice_data: "invoice_1.pdf")

    result = handler.handle_generate_invoice_pdf("inv-1", user_id="u-1")

    assert result == {"status": "ok", "storage_key": "invoice_1.pdf"}
    assert supabase.updated_document_payload == {"storage_key": "invoice_1.pdf"}


def test_handle_generate_invoice_pdf_rejects_non_invoice():
    class _NonInvoiceSupabase(_SupabaseStub):
        def table(self, table_name):
            query = super().table(table_name)
            original_execute = query.execute

            def _execute():
                result = original_execute()
                if table_name == "document" and query._op == "select" and result.data:
                    result.data["type"] = "QUOTE"
                return result

            query.execute = _execute
            return query

    handler = InvoiceHandlers(supabase=_NonInvoiceSupabase())

    result = handler.handle_generate_invoice_pdf("inv-1", user_id="u-1")

    assert result == {"status": "error", "message": "PDF generation is only supported for invoices"}
