"""Quote controller service shared by FastAPI transport."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.storage_paths import get_storage_dir, get_storage_path
from src.service.quote.service import QuoteService


class QuoteController:
    """Quote application service for update/pdf/list/download flows."""

    def __init__(self, quote_service: QuoteService = None):
        self.quote_service = quote_service or QuoteService()

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        return self.quote_service.update(document_id=document_id, payload=payload, user_id=user_id)

    def safe_numeric(self, value):
        return self.quote_service.safe_numeric(value)

    def handle_quote_submit(self, payload):
        try:
            if isinstance(payload, (bytes, bytearray)):
                payload = json.loads(payload.decode("utf-8"))
            elif isinstance(payload, str):
                payload = json.loads(payload)

            if not payload or "products" not in payload:
                return {
                    "status": "error",
                    "message": "Invalid quote data: missing products",
                }

            pdf_filename = self._generate_quote_pdf(payload)
            return {
                "status": "ok",
                "message": "Quote received and PDF generated successfully",
                "pdf_filename": pdf_filename,
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in request body",
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error processing quote: {str(exc)}",
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

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def handle_list_quotes(self) -> Dict:
        try:
            assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            pdf_files = sorted([f.name for f in assets_dir.glob("quote_*.pdf")], reverse=True)
            return {"status": "ok", "quotes": pdf_files, "total": len(pdf_files)}
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error listing quotes: {str(exc)}",
            }

    def handle_get_quote_file(self, filename: str) -> bytes:
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
        except Exception as exc:
            raise FileNotFoundError(f"Error retrieving quote: {str(exc)}")

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
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
                quantity = self._safe_float(line.get("quantity", 1), default=1.0)
                unit_price_excl_tax = self._safe_float(
                    line.get("unit_price_excl_tax", line.get("unit_price", line.get("selling_price", line.get("price", 0)))),
                    default=0.0,
                )
                client_discount_rate = self._safe_float(line.get("client_discount_rate", 0), default=0.0)
                discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)
                line_total_excl_tax = self._safe_float(
                    line.get("line_total_excl_tax", line.get("total_excl_tax", 0)),
                    default=0.0,
                )
                if line_total_excl_tax <= 0:
                    line_total_excl_tax = quantity * discounted_unit_price
                tax_rate = self._safe_float(line.get("tax_rate", 20), default=20.0)

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
                        "unit_price": discounted_unit_price,
                        "unit_price_excl_tax": unit_price_excl_tax,
                        "client_discount_rate": client_discount_rate,
                        "discounted_unit_price": discounted_unit_price,
                        "line_total_excl_tax": line_total_excl_tax,
                        "line_total": line_total_excl_tax,
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
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error generating PDF: {str(exc)}",
            }

    def handle_generate_quote_pdf_from_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        _ = user_id
        supabase = get_supabase_service()

        try:
            quote_resp = (
                supabase.table("document")
                .select("id")
                .eq("opportunity_id", opportunity_id)
                .eq("type", "QUOTE")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if getattr(quote_resp, "error", None):
                return {"status": "error", "message": f"Quote lookup failed: {quote_resp.error}"}

            if not quote_resp.data:
                return {"status": "error", "message": f"No quote found for opportunity {opportunity_id}"}

            document_id = quote_resp.data[0].get("id")
            if not document_id:
                return {"status": "error", "message": "Invalid quote document id"}

            return self.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error generating quote PDF from opportunity: {str(exc)}",
            }

    @staticmethod
    def _normalize_account_address(account: Dict) -> Dict[str, str]:
        account = account or {}
        street_address = account.get("street_address") or account.get("address_line1") or account.get("address1") or ""
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
        storage_dir = self._get_storage_dir("quote")
        storage_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path(__file__).resolve().parents[3] / "templates"

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
            return f"{integer_part},{decimal_part}" if decimal_part else integer_part

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
            quantity = self._safe_float(product.get("quantity", 1), default=1.0)
            unit_price_excl_tax = self._safe_float(
                product.get("unit_price_excl_tax", product.get("unit_price", product.get("selling_price", product.get("price", 0)))),
                default=0.0,
            )
            client_discount_rate = self._safe_float(product.get("client_discount_rate", 0), default=0.0)

            discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)
            line_total_excl_tax = self._safe_float(
                product.get("line_total_excl_tax", product.get("line_total", 0)),
                default=0.0,
            )
            if line_total_excl_tax <= 0:
                line_total_excl_tax = quantity * discounted_unit_price

            template_data["products"].append(
                {
                    "quantity": quantity,
                    "brand": product.get("brand", "") or product.get("manufacturer", ""),
                    "manufacturer": product.get("manufacturer", ""),
                    "sku": product.get("sku", ""),
                    "description": product.get("description", ""),
                    "price": unit_price_excl_tax,
                    "unit_price": discounted_unit_price,
                    "unit_price_excl_tax": unit_price_excl_tax,
                    "discounted_unit_price": discounted_unit_price,
                    "client_discount_rate": client_discount_rate,
                    "line_total_excl_tax": line_total_excl_tax,
                    "line_total": line_total_excl_tax,
                    "selling_price": product.get("selling_price"),
                    "price_found": unit_price_excl_tax > 0,
                }
            )

        html_content = template.render(**template_data)
        HTML(string=html_content).write_pdf(str(pdf_path))
        return pdf_filename
