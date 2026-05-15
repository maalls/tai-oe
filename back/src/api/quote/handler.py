import json
import os
import uuid
from pathlib import Path
from typing import Dict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.api.routes.server_auth_helpers import require_auth
from src.api.routes.server_body_helpers import read_body, read_json
from src.service.quote.service import QuoteService
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.storage_paths import get_storage_dir, get_storage_path
import yaml


class Quote:

    def __init__(self, quote_service: QuoteService = None):
        self.quote_service = quote_service or QuoteService()

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        return self.quote_service.update(document_id=document_id, payload=payload, user_id=user_id)
            
    def safe_numeric(self, value):
        return self.quote_service.safe_numeric(value)

    def handle_quote_submit(self, payload):
        """Handle quote submission and generate PDF.
        
        Parameters
        ----------
        body : bytes
            Raw JSON body with RFP data
        content_type : str
            Content-Type header value
        
        Returns
        -------
        Dict
            Response with status, message, and PDF filename
        """
        try:
            # Parse JSON payload when needed
            if isinstance(payload, (bytes, bytearray)):
                payload = json.loads(payload.decode('utf-8'))
            elif isinstance(payload, str):
                payload = json.loads(payload)
            
            # Validate structure
            if not payload or 'products' not in payload:
                return {
                    "status": "error",
                    "message": "Invalid quote data: missing products"
                }
            
            # Generate PDF
            pdf_filename = self._generate_quote_pdf(payload)
            
            # Log the received quote
            print(f"[QuoteController] Quote received with {len(payload.get('products', []))} products")
            print(f"[QuoteController] PDF generated: {pdf_filename}")
            
            return {
                "status": "ok",
                "message": "Quote received and PDF generated successfully",
                "pdf_filename": pdf_filename
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in request body"
            }
        except Exception as e:
            print(f"[QuoteController] Error in handle_quote_submit: {e}")
            return {
                "status": "error",
                "message": f"Error processing quote: {str(e)}"
            }
        
    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        self.quote_service.update_line_from_product(document=document, product=product)
        
    def _compute_document_totals(self, lines: list) -> Dict[str, float]:
        return self.quote_service._compute_document_totals(lines)
    
    def _compute_totals(self, rfp_data: Dict) -> Dict[str, float]:
        return self.quote_service._compute_totals(rfp_data)

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        return get_storage_dir(source)

    @staticmethod
    def _get_storage_path(source: str, filename: str) -> Path:
        return get_storage_path(source, filename)

    def handle_list_quotes(self) -> Dict:
        """List all generated quote files."""
        try:
            assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            pdf_files = sorted(
                [f.name for f in assets_dir.glob("quote_*.pdf")],
                reverse=True,
            )

            return {
                "status": "ok",
                "quotes": pdf_files,
                "total": len(pdf_files),
            }
        except Exception as e:  # noqa: BLE001
            print(f"[QuoteController] Error listing quotes: {e}")
            return {
                "status": "error",
                "message": f"Error listing quotes: {str(e)}",
            }

    def handle_get_quote_file(self, filename: str) -> bytes:
        """Retrieve a quote PDF file from storage."""
        try:
            if not filename.startswith("quote_") or not filename.endswith(".pdf"):
                raise ValueError(f"Invalid filename format: {filename}")

            pdf_path = self._get_storage_path("quote", filename)

            if not pdf_path.exists():
                legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                legacy_pdf_path = legacy_assets_dir / filename

                if legacy_pdf_path.exists():
                    pdf_path = legacy_pdf_path
                else:
                    raise FileNotFoundError(f"Quote file not found: {filename}")

            return pdf_path.read_bytes()
        except FileNotFoundError:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[QuoteController] Error retrieving quote: {e}")
            raise FileNotFoundError(f"Error retrieving quote: {str(e)}")

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

    def _generate_quote_pdf(self, rfp_data: Dict) -> str:
        """Generate PDF from quote-like data using the quote template."""
        storage_dir = self._get_storage_dir("quote")
        storage_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path(__file__).parent.parent.parent / "templates"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quote_id_num = str(uuid.uuid4())[:8]
        pdf_filename = f"quote_{timestamp}_{quote_id_num}.pdf"
        pdf_path = storage_dir / pdf_filename

        env = Environment(loader=FileSystemLoader(str(templates_dir)))

        def format_currency(value, currency):
            try:
                value = float(value)
            except (TypeError, ValueError):
                return "0,00"

            if currency.upper() in ["JPY", "YEN", "KRW", "CNY", "RUB"]:
                decimals = 0
            elif currency.upper() in ["BHD", "JOD", "KWD", "OMR", "TND"]:
                decimals = 3
            else:
                decimals = 2

            formatted = f"{value:,.{decimals}f}"
            parts = formatted.split(".")
            integer_part = parts[0].replace(",", " ")
            decimal_part = parts[1] if len(parts) > 1 else ""

            if decimal_part:
                return f"{integer_part},{decimal_part}"
            return integer_part

        env.filters["format_currency"] = format_currency
        template = env.get_template("quote.html")

        template_data = {
            "quote_id": rfp_data.get("quote_id", f"QT-{quote_id_num}"),
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "issued_date": rfp_data.get("issued_date", ""),
            "valid_until": rfp_data.get("valid_until", ""),
            "title": rfp_data.get("title", ""),
            "contact": rfp_data.get("contact", {}),
            "account": rfp_data.get("account", {}),
            "products": [],
            "currency": rfp_data.get("currency", "EUR"),
            "totals": rfp_data.get("totals", {}),
        }

        for product in rfp_data.get("products", []):
            try:
                quantity = float(product.get("quantity", 1) or 1)
            except Exception:
                quantity = 1.0

            try:
                unit_price_excl_tax = float(product.get("unit_price_excl_tax", product.get("price", 0)) or 0)
            except Exception:
                unit_price_excl_tax = 0.0

            try:
                client_discount_rate = float(product.get("client_discount_rate", 0) or 0)
            except Exception:
                client_discount_rate = 0.0

            discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)

            try:
                line_total_excl_tax = float(product.get("line_total_excl_tax"))
            except Exception:
                line_total_excl_tax = quantity * discounted_unit_price

            template_data["products"].append(
                {
                    "quantity": quantity,
                    "brand": product.get("brand", "") or product.get("manufacturer", ""),
                    "manufacturer": product.get("manufacturer", ""),
                    "sku": product.get("sku", ""),
                    "description": product.get("description", ""),
                    "price": unit_price_excl_tax,
                    "unit_price_excl_tax": unit_price_excl_tax,
                    "discounted_unit_price": discounted_unit_price,
                    "client_discount_rate": client_discount_rate,
                    "line_total_excl_tax": line_total_excl_tax,
                    "selling_price": product.get("selling_price"),
                    "price_found": unit_price_excl_tax > 0,
                }
            )

        html_content = template.render(**template_data)
        HTML(string=html_content).write_pdf(str(pdf_path))
        return pdf_filename


def handle_quote_submit_post(handler):
    """Handle /api/quote POST endpoint."""
    content_type = handler.headers.get('Content-Type', '')
    body = read_body(handler)
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_quote_submit(body, content_type)
    return handler.json(result)


def handle_quote_send_post(handler):
    """Handle /api/quote/send POST endpoint."""
    print(f"[RAG] Received request to send quote email, path: /api/quote/send, method: {handler.command}")
    content_type = handler.headers.get('Content-Type', '')
    body = read_body(handler)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_quote_send(body, content_type)
    return handler.json(result)


def handle_quote_update_post(handler, quote_update_match):
    """Handle /api/quote/{id} POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    document_id = quote_update_match.group(1)
    payload = read_json(handler, default={})

    print(f"[RAG] Updating quote {document_id} by user {user_id} with payload: {payload}")
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_update_quote(document_id=document_id, payload=payload, user_id=user_id)
    status = handler._status_from_error(result)
    return handler.json(result, status)


def handle_quote_pdf_post(handler, quote_pdf_match):
    """Handle /api/quote/{id}/pdf POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    document_id = quote_pdf_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_quotes_list_get(handler, request_handlers):
    """Handle /api/quotes/list GET endpoint."""
    return handler.json(request_handlers.handle_list_quotes())


def handle_quotes_download_get(handler, parsed_path: str, qs, request_handlers):
    """Handle /api/quotes/download/<filename> GET endpoint."""
    filename = parsed_path.split('/api/quotes/download/')[-1]
    return handle_quote_download(handler, filename, request_handlers, qs)


def handle_quote_download(handler, filename, request_handlers, qs=None):
    """Stream PDF quote file."""
    try:
        qs = qs or {}
        is_inline = qs.get('inline', ['0'])[0] == '1'
        content = request_handlers.handle_get_quote_file(filename)
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/pdf')
        disposition = 'inline' if is_inline else 'attachment'
        handler.send_header('Content-Disposition', f'{disposition}; filename="{filename}"')
        handler.send_header('Content-Length', str(len(content)))
        handler.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
        handler.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        handler.send_header('Access-Control-Allow-Credentials', 'true')
        handler._cors_header_sent = True
        handler.end_headers()
        handler.wfile.write(content)
    except FileNotFoundError:
        return handler._send_error(404, 'Quote file not found')
    except Exception as e:
        return handler._send_error(500, f"Error streaming PDF: {e}")

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate a PDF for an existing quote document and update storage_key."""
        _ = user_id
        supabase = get_supabase_service()

        try:
            doc_resp = supabase.table("document").select("*").eq("id", document_id).single().execute()
            if getattr(doc_resp, "error", None):
                return {"status": "error", "message": f"Document lookup failed: {doc_resp.error}"}
            document = doc_resp.data
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "PDF generation is only supported for quotes"}

            opportunity_id = document.get("opportunity_id")
            account = {}

            if opportunity_id:
                opp_resp = supabase.table("opportunity").select("*").eq("id", opportunity_id).single().execute()
                if not getattr(opp_resp, "error", None) and opp_resp.data:
                    account_id = opp_resp.data.get("account_id")
                    if account_id:
                        acc_resp = supabase.table("account").select("*").eq("id", account_id).single().execute()
                        if not getattr(acc_resp, "error", None) and acc_resp.data:
                            account = acc_resp.data

            line_resp = supabase.table("document_line").select("*").eq("document_id", document_id).order("position").execute()
            if getattr(line_resp, "error", None):
                return {"status": "error", "message": f"Document lines lookup failed: {line_resp.error}"}
            lines = line_resp.data or []

            rfp_data = {
                "quote_id": document.get("id"),
                "title": document.get("title") or "Quote",
                "products": [],
                "contact": {
                    "company_name": account.get("name", ""),
                    "address": self._normalize_account_address(account),
                },
                "account": account,
                "issued_date": document.get("issued_at") or datetime.now().isoformat(),
                "valid_until": document.get("valid_until"),
                "currency": document.get("currency", "EUR"),
                "totals": {"subtotal": 0.0, "tax": 0.0, "total": 0.0},
            }

            computed_subtotal = 0.0
            computed_tax = 0.0
            for line in lines:
                quantity = float(line.get("quantity", 1) or 1)
                unit_price_excl_tax = float(line.get("unit_price_excl_tax", 0) or 0)
                client_discount_rate = float(line.get("client_discount_rate", 0) or 0)
                discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)
                line_total_excl_tax = float(line.get("line_total_excl_tax", 0) or 0)
                if line_total_excl_tax <= 0:
                    line_total_excl_tax = quantity * discounted_unit_price
                tax_rate = float(line.get("tax_rate", 20) or 20)

                computed_subtotal += line_total_excl_tax
                computed_tax += line_total_excl_tax * (tax_rate / 100.0)

                rfp_data["products"].append(
                    {
                        "quantity": quantity,
                        "brand": line.get("brand", ""),
                        "manufacturer": line.get("brand", ""),
                        "sku": line.get("sku"),
                        "description": line.get("description"),
                        "price": unit_price_excl_tax,
                        "unit_price_excl_tax": unit_price_excl_tax,
                        "client_discount_rate": client_discount_rate,
                        "discounted_unit_price": discounted_unit_price,
                        "line_total_excl_tax": line_total_excl_tax,
                        "tax_rate": tax_rate,
                        "unit": line.get("unit", "U"),
                    }
                )

            computed_subtotal = round(computed_subtotal, 2)
            computed_tax = round(computed_tax, 2)
            computed_total = round(computed_subtotal + computed_tax, 2)
            rfp_data["totals"] = {
                "subtotal": computed_subtotal,
                "tax": computed_tax,
                "total": computed_total,
            }

            pdf_filename = self._generate_quote_pdf(rfp_data)

            update_payload = {
                "storage_key": pdf_filename,
                "total_excl_tax": computed_subtotal,
                "total_tax": computed_tax,
                "total_incl_tax": computed_total,
            }

            upd_resp = supabase.table("document").update(update_payload).eq("id", document_id).execute()
            if getattr(upd_resp, "error", None):
                fallback_resp = supabase.table("document").update({"storage_key": pdf_filename}).eq("id", document_id).execute()
                if getattr(fallback_resp, "error", None):
                    return {
                        "status": "error",
                        "message": f"Failed to update document with PDF: {fallback_resp.error}",
                    }

            return {"status": "ok", "pdf_filename": pdf_filename}

        except Exception as e:  # noqa: BLE001
            print(f"[QuoteController] Error generating PDF for document {document_id}: {e}")
            return {
                "status": "error",
                "message": f"Error generating PDF: {str(e)}",
            }


