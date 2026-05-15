"""Invoice-related request handlers."""

from datetime import datetime
from pathlib import Path
from typing import Dict
import uuid

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.infrastructure.clients.supabase import get_supabase_service


class InvoiceHandlers:
    """Handle invoice-related API requests."""

    def __init__(self, supabase=None):
        self.supabase = supabase or get_supabase_service()

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
            try:
                pdf_result = self.handle_generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
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

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        base_storage = Path("var/storage")
        source_map = {
            "rfp_upload": "rfp_uploads",
            "email": "emails",
            "quote": "quotes",
            "invoice": "invoices",
            "attachment": "attachments",
        }
        subdir = source_map.get(source, source)
        return base_storage / subdir

    @staticmethod
    def _normalize_account_address(account: Dict) -> Dict[str, str]:
        account = account or {}
        street_address = (
            account.get("street_address")
            or account.get("address_line1")
            or account.get("address1")
            or ""
        )
        address_line2 = account.get("address_line2") or account.get("address2") or ""
        city = account.get("city") or ""
        postal_code = account.get("postal_code") or ""
        country_name = account.get("country_name") or account.get("country") or ""

        return {
            "street_address": street_address,
            "address_line1": account.get("address_line1") or street_address,
            "address_line2": address_line2,
            "city": city,
            "postal_code": postal_code,
            "country_name": country_name,
        }

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate a PDF for an existing invoice document and update storage_key."""
        _ = user_id
        try:
            doc_resp = self.supabase.table("document").select("*").eq("id", document_id).single().execute()
            if getattr(doc_resp, "error", None):
                return {"status": "error", "message": f"Document lookup failed: {doc_resp.error}"}
            document = doc_resp.data
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}

            if document.get("type") != "INVOICE":
                return {"status": "error", "message": "PDF generation is only supported for invoices"}

            opportunity_id = document.get("opportunity_id")
            account_id = None
            account = {}

            if opportunity_id:
                opp_resp = self.supabase.table("opportunity").select("*").eq("id", opportunity_id).single().execute()
                if not getattr(opp_resp, "error", None) and opp_resp.data:
                    account_id = opp_resp.data.get("account_id")
                    if account_id:
                        acc_resp = self.supabase.table("account").select("*").eq("id", account_id).single().execute()
                        if not getattr(acc_resp, "error", None) and acc_resp.data:
                            account = acc_resp.data

            line_resp = (
                self.supabase.table("document_line")
                .select("*")
                .eq("document_id", document_id)
                .order("position")
                .execute()
            )
            if getattr(line_resp, "error", None):
                return {"status": "error", "message": f"Document lines lookup failed: {line_resp.error}"}
            lines = line_resp.data or []

            invoice_data = {
                "invoice_id": document.get("id"),
                "external_ref": document.get("external_ref") or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": document.get("title") or "Invoice",
                "products": [],
                "contact": {
                    "company_name": account.get("name", ""),
                    "address": self._normalize_account_address(account),
                },
                "account": account,
                "issued_date": document.get("issued_at") or datetime.now().isoformat(),
                "currency": document.get("currency", "EUR"),
                "totals": {
                    "subtotal": float(document.get("total_excl_tax", 0)),
                    "tax": float(document.get("total_tax", 0)),
                    "total": float(document.get("total_incl_tax", 0)),
                },
            }

            for line in lines:
                invoice_data["products"].append(
                    {
                        "quantity": float(line.get("quantity", 1)),
                        "manufacturer": line.get("brand", ""),
                        "sku": line.get("sku"),
                        "description": line.get("description"),
                        "price": float(line.get("unit_price_excl_tax", 0)),
                        "tax_rate": float(line.get("tax_rate", 20)),
                        "unit": line.get("unit", "U"),
                    }
                )

            pdf_filename = self._generate_invoice_pdf(invoice_data)

            upd_resp = self.supabase.table("document").update({"storage_key": pdf_filename}).eq("id", document_id).execute()
            if getattr(upd_resp, "error", None):
                return {"status": "error", "message": f"Failed to update document with PDF: {upd_resp.error}"}

            return {"status": "ok", "storage_key": pdf_filename}

        except Exception as e:  # noqa: BLE001
            print(f"[InvoiceHandlers] Error generating PDF for invoice {document_id}: {e}")
            return {"status": "error", "message": f"Error generating PDF: {str(e)}"}

    def _generate_invoice_pdf(self, invoice_data: Dict) -> str:
        """Generate PDF from invoice data using HTML template."""
        storage_dir = self._get_storage_dir("invoice")
        storage_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path(__file__).parent.parent.parent / "templates"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        invoice_id_num = str(uuid.uuid4())[:8]
        pdf_filename = f"invoice_{timestamp}_{invoice_id_num}.pdf"
        pdf_path = storage_dir / pdf_filename

        env = Environment(loader=FileSystemLoader(str(templates_dir)))

        def format_currency(value, currency):
            if currency.upper() in ["JPY", "YEN", "KRW", "CNY", "RUB"]:
                decimals = 0
            elif currency.upper() in ["BHD", "JOD", "KWD", "OMR", "TND"]:
                decimals = 3
            else:
                decimals = 2
            return f"{float(value):.{decimals}f}"

        env.filters["format_currency"] = format_currency
        template = env.get_template("invoice.html")

        template_data = {
            "quote_id": invoice_data.get("external_ref", f"INV-{invoice_id_num}"),
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "issued_date": invoice_data.get("issued_date", ""),
            "title": invoice_data.get("title", ""),
            "contact": invoice_data.get("contact", {}),
            "account": invoice_data.get("account", {}),
            "products": [],
            "currency": invoice_data.get("currency", "EUR"),
            "totals": invoice_data.get("totals", {}),
        }

        for product in invoice_data.get("products", []):
            template_data["products"].append(
                {
                    "quantity": product.get("quantity", 1),
                    "manufacturer": product.get("manufacturer", ""),
                    "part_number": product.get("sku", ""),
                    "description": product.get("description", ""),
                    "price": product.get("price", 0),
                    "price_found": product.get("price", 0) > 0,
                }
            )

        html_content = template.render(**template_data)
        HTML(string=html_content).write_pdf(str(pdf_path))
        return pdf_filename
