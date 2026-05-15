"""Invoice-related request handlers."""

from datetime import datetime
from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service


class InvoiceHandlers:
    """Handle invoice-related API requests."""

    def __init__(self, supabase=None, generate_invoice_pdf: Callable = None):
        self.supabase = supabase or get_supabase_service()
        self.generate_invoice_pdf = generate_invoice_pdf

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        """Generate an invoice document from an accepted quote."""
        try:
            quote_resp = self.supabase.table("document").select("*").eq("id", quote_id).execute()

            if not quote_resp.data or len(quote_resp.data) == 0:
                quote_resp = (
                    self.supabase.table("document")
                    .select("*")
                    .eq("opportunity_id", quote_id)
                    .eq("type", "QUOTE")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

            if getattr(quote_resp, "error", None) or not quote_resp.data:
                return {"status": "error", "message": f"Quote not found for {quote_id}"}

            quote = quote_resp.data[0]
            if quote.get("type") != "QUOTE":
                return {"status": "error", "message": "Document must be a QUOTE"}

            quote_document_id = quote.get("id")

            existing_resp = (
                self.supabase.table("document")
                .select("id")
                .eq("parent_document_id", quote_document_id)
                .eq("type", "INVOICE")
                .execute()
            )
            if existing_resp.data and len(existing_resp.data) > 0:
                return {"status": "error", "message": "Invoice already exists for this quote"}

            lines_resp = (
                self.supabase.table("document_line")
                .select("*")
                .eq("document_id", quote_document_id)
                .order("position")
                .execute()
            )
            if getattr(lines_resp, "error", None):
                return {"status": "error", "message": f"Failed to load quote lines: {lines_resp.error}"}
            lines = lines_resp.data or []

            invoice_data = {
                "type": "INVOICE",
                "status": "DRAFT",
                "opportunity_id": quote.get("opportunity_id"),
                "parent_document_id": quote_document_id,
                "title": f"Invoice - {quote.get('title', 'Quote')}",
                "external_ref": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "currency": quote.get("currency", "EUR"),
                "total_excl_tax": quote.get("total_excl_tax", 0),
                "total_tax": quote.get("total_tax", 0),
                "total_incl_tax": quote.get("total_incl_tax", 0),
                "issued_at": datetime.now().isoformat(),
            }

            inv_resp = self.supabase.table("document").insert([invoice_data]).execute()
            if getattr(inv_resp, "error", None) or not inv_resp.data:
                return {"status": "error", "message": f"Failed to create invoice: {inv_resp.error}"}

            invoice_id = inv_resp.data[0]["id"]

            invoice_lines = []
            for line in lines:
                invoice_lines.append(
                    {
                        "document_id": invoice_id,
                        "position": line.get("position"),
                        "sku": line.get("sku"),
                        "brand": line.get("brand"),
                        "description": line.get("description"),
                        "quantity": line.get("quantity"),
                        "unit": line.get("unit"),
                        "unit_price_excl_tax": line.get("unit_price_excl_tax"),
                        "tax_rate": line.get("tax_rate"),
                        "line_total_excl_tax": line.get("line_total_excl_tax"),
                    }
                )

            if invoice_lines:
                line_insert_resp = self.supabase.table("document_line").insert(invoice_lines).execute()
                if getattr(line_insert_resp, "error", None):
                    return {
                        "status": "error",
                        "message": f"Failed to copy lines to invoice: {line_insert_resp.error}",
                    }

            storage_key = None
            if self.generate_invoice_pdf is not None:
                try:
                    pdf_result = self.generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
                    if pdf_result.get("status") == "ok":
                        storage_key = pdf_result.get("storage_key")
                except Exception as pdf_error:  # noqa: BLE001
                    print(f"[InvoiceHandlers] Warning: Error auto-generating invoice PDF: {pdf_error}")

            return {
                "status": "ok",
                "invoice_id": invoice_id,
                "invoice": {
                    "id": invoice_id,
                    "title": invoice_data["title"],
                    "external_ref": invoice_data["external_ref"],
                    "currency": invoice_data["currency"],
                    "storage_key": storage_key,
                    "totals": {
                        "subtotal": invoice_data["total_excl_tax"],
                        "tax": invoice_data["total_tax"],
                        "total": invoice_data["total_incl_tax"],
                    },
                },
            }

        except Exception as e:  # noqa: BLE001
            print(f"[InvoiceHandlers] Error generating invoice from quote {quote_id}: {e}")
            return {"status": "error", "message": f"Error generating invoice: {str(e)}"}
