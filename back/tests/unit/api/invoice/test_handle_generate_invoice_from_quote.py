"""Unit tests for InvoiceHandlers.handle_generate_invoice_from_quote."""

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

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "select":
            if self._filters.get("id") == "quote-1":
                return _Response(
                    data=[
                        {
                            "id": "quote-1",
                            "type": "QUOTE",
                            "opportunity_id": "opp-1",
                            "title": "Quote A",
                            "currency": "EUR",
                            "total_excl_tax": 100,
                            "total_tax": 20,
                            "total_incl_tax": 120,
                        }
                    ]
                )
            if self._filters.get("parent_document_id") == "quote-1" and self._filters.get("type") == "INVOICE":
                if self.supabase.invoice_already_exists:
                    return _Response(data=[{"id": "inv-existing"}])
                return _Response(data=[])
            if self._filters.get("opportunity_id") == "opp-1" and self._filters.get("type") == "QUOTE":
                return _Response(
                    data=[
                        {
                            "id": "quote-1",
                            "type": "QUOTE",
                            "opportunity_id": "opp-1",
                            "title": "Quote A",
                            "currency": "EUR",
                            "total_excl_tax": 100,
                            "total_tax": 20,
                            "total_incl_tax": 120,
                        }
                    ]
                )
            return _Response(data=[])

        if self.table_name == "document_line" and self._op == "select":
            return _Response(
                data=[
                    {
                        "position": 1,
                        "sku": "SKU-1",
                        "brand": "Brand",
                        "description": "Desc",
                        "quantity": 2,
                        "unit": "U",
                        "unit_price_excl_tax": 50,
                        "tax_rate": 20,
                        "line_total_excl_tax": 100,
                    }
                ]
            )

        if self.table_name == "document" and self._op == "insert":
            self.supabase.inserted_invoice = self._payload
            return _Response(data=[{"id": "inv-1"}])

        if self.table_name == "document_line" and self._op == "insert":
            self.supabase.inserted_invoice_lines = self._payload
            return _Response(data=self._payload)

        return _Response(data=[])


class _SupabaseStub:
    def __init__(self):
        self.invoice_already_exists = False
        self.inserted_invoice = None
        self.inserted_invoice_lines = None

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_generate_invoice_from_quote_success_calls_pdf_generation():
    supabase = _SupabaseStub()
    pdf_calls = []

    def _generate_invoice_pdf(document_id: str, user_id: str = None):
        pdf_calls.append((document_id, user_id))
        return {"status": "ok", "storage_key": "invoice_1.pdf"}

    handler = InvoiceHandlers(supabase=supabase, generate_invoice_pdf=_generate_invoice_pdf)

    result = handler.handle_generate_invoice_from_quote("quote-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["invoice_id"] == "inv-1"
    assert result["invoice"]["storage_key"] == "invoice_1.pdf"
    assert pdf_calls == [("inv-1", "u-1")]
    assert supabase.inserted_invoice is not None
    assert supabase.inserted_invoice_lines is not None


def test_handle_generate_invoice_from_quote_supports_opportunity_id_lookup():
    supabase = _SupabaseStub()
    handler = InvoiceHandlers(
        supabase=supabase,
        generate_invoice_pdf=lambda document_id, user_id=None: {"status": "ok", "storage_key": f"{document_id}.pdf"},
    )

    result = handler.handle_generate_invoice_from_quote("opp-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["invoice_id"] == "inv-1"


def test_handle_generate_invoice_from_quote_rejects_existing_invoice():
    supabase = _SupabaseStub()
    supabase.invoice_already_exists = True
    handler = InvoiceHandlers(supabase=supabase, generate_invoice_pdf=lambda document_id, user_id=None: {"status": "ok"})

    result = handler.handle_generate_invoice_from_quote("quote-1", user_id="u-1")

    assert result == {"status": "error", "message": "Invoice already exists for this quote"}
