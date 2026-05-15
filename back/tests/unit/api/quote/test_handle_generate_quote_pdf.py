"""Unit tests for Quote.handle_generate_quote_pdf."""

from src.api.quote.handler import Quote


class _Response:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _TableQuery:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self._op = None
        self._eq = {}
        self._update_payload = None

    def select(self, *_args, **_kwargs):
        self._op = "select"
        return self

    def update(self, payload):
        self._op = "update"
        self._update_payload = payload
        return self

    def eq(self, field, value):
        self._eq[field] = value
        return self

    def single(self):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "select":
            return _Response(
                {
                    "id": "doc-q-1",
                    "type": "QUOTE",
                    "opportunity_id": "opp-1",
                    "title": "Quote",
                    "currency": "EUR",
                }
            )
        if self.table_name == "opportunity" and self._op == "select":
            return _Response({"id": "opp-1", "account_id": "acc-1"})
        if self.table_name == "account" and self._op == "select":
            return _Response({"id": "acc-1", "name": "ACME"})
        if self.table_name == "document_line" and self._op == "select":
            return _Response([
                {
                    "sku": "SKU-1",
                    "quantity": 2,
                    "unit_price_excl_tax": 10,
                    "line_total_excl_tax": 20,
                    "tax_rate": 20,
                    "description": "desc",
                    "brand": "brand",
                    "unit": "U",
                    "client_discount_rate": 0,
                }
            ])
        if self.table_name == "document" and self._op == "update":
            self.supabase.last_update = self._update_payload
            return _Response([{"id": "doc-q-1"}])

        return _Response(None)


class _SupabaseStub:
    def __init__(self):
        self.last_update = None

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_generate_quote_pdf_updates_document(monkeypatch):
    supabase = _SupabaseStub()
    monkeypatch.setattr("src.api.quote.handler.get_supabase_service", lambda: supabase)

    quote_handler = Quote.__new__(Quote)
    monkeypatch.setattr(quote_handler, "_generate_quote_pdf", lambda _rfp_data: "quote_test.pdf")

    result = quote_handler.handle_generate_quote_pdf("doc-q-1", user_id="u-1")

    assert result == {"status": "ok", "pdf_filename": "quote_test.pdf"}
    assert supabase.last_update is not None
    assert supabase.last_update["storage_key"] == "quote_test.pdf"
