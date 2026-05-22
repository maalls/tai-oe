"""Application service for quote operations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.lib.storage_paths import get_storage_dir, get_storage_path
from src.repository.opportunity import OpportunityRepository


class QuoteService:
    """Service that encapsulates quote business operations."""

    def __init__(self, opportunity_repository=None, db_handler: DatabaseHandler | None = None):
        self.opportunity_repository = opportunity_repository or OpportunityRepository()
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    @staticmethod
    def _as_float(value, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        del user_id
        try:
            print(f"[QuoteService][update] Updating document {document_id}", payload)

            doc_fields = payload.copy()
            lines_payload = payload.get("document_line", [])
            print(f"[QuoteService][update] Processing {len(lines_payload)} lines")

            new_lines = []
            for idx, line in enumerate(lines_payload):
                print(f"[QuoteService][update] Processing line {idx}", line)

                brand = line.get("brand")
                if brand and not isinstance(brand, str):
                    raise ValueError(f"Brand must be a string, got {type(brand)} for line {idx}")

                client_discount_rate = self.safe_numeric(line.get("client_discount_rate"))
                quantity = self._as_float(line.get("quantity"), default=0.0)
                unit_price_excl_tax = self._as_float(
                    line.get("unit_price_excl_tax", line.get("price")),
                    default=0.0,
                )

                line_total_excl_tax = self._as_float(line.get("line_total_excl_tax"), default=0.0)
                if line_total_excl_tax <= 0:
                    line_total_excl_tax = quantity * unit_price_excl_tax * (1 - (client_discount_rate / 100.0))

                line_total_excl_tax = round(line_total_excl_tax, 2)

                new_lines.append({
                    "id": line.get("id") or str(uuid.uuid4()),
                    "document_id": document_id,
                    "position": idx + 1,
                    "description": line.get("description", ""),
                    "quantity": quantity,
                    "unit_price_excl_tax": unit_price_excl_tax,
                    "tax_rate": line.get("tax_rate", 0),
                    "sku": line.get("sku", ""),
                    "brand": brand or "",
                    "unit": line.get("unit", ""),
                    "discount_rate": self.safe_numeric(line.get("discount_rate")),
                    "client_discount_rate": client_discount_rate,
                    "line_total_excl_tax": line_total_excl_tax,
                })

            totals = self._compute_document_totals(new_lines)
            print(f"[QuoteService][update] Computed totals: {totals}")

            self._replace_document_lines_atomic(
                document_id=document_id,
                title=doc_fields.get("title"),
                currency=doc_fields.get("currency"),
                new_lines=new_lines,
                totals=totals,
            )

            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (document_id,),
            )
            if not rows:
                raise ValueError(f"Document {document_id} not found")
            document = rows[0]
            document_lines = self._get_db_handler().execute_dict_query(
                "SELECT * FROM document_line WHERE document_id = %s ORDER BY position",
                (document_id,),
            )
            document["document_line"] = document_lines
            return document
        except Exception as e:
            print(f"[QuoteService][update] Error updating quote: {e}")
            raise e

    def _replace_document_lines_atomic(
        self,
        document_id: str,
        title: str,
        currency: str,
        new_lines: list,
        totals: Dict[str, float],
    ) -> None:
        if self.db_handler is None:
            raise ValueError("QuoteService requires an injected db_handler for atomic line replacement")
        db_handler = self.db_handler

        with db_handler.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE document
                    SET title = %s,
                        currency = %s,
                        total_excl_tax = %s,
                        total_tax = %s,
                        total_incl_tax = %s
                    WHERE id = %s
                    """,
                    (
                        title,
                        currency,
                        totals["total_excl_tax"],
                        totals["total_tax"],
                        totals["total_incl_tax"],
                        document_id,
                    ),
                )

                cur.execute("DELETE FROM document_line WHERE document_id = %s", (document_id,))

                if not new_lines:
                    return

                cur.executemany(
                    """
                    INSERT INTO document_line (
                        id,
                        document_id,
                        position,
                        description,
                        quantity,
                        unit_price_excl_tax,
                        tax_rate,
                        sku,
                        brand,
                        unit,
                        discount_rate,
                        client_discount_rate,
                        line_total_excl_tax
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            line["id"],
                            document_id,
                            line.get("position"),
                            line.get("description", ""),
                            line.get("quantity", 0),
                            line.get("unit_price_excl_tax", 0),
                            line.get("tax_rate", 0),
                            line.get("sku", ""),
                            line.get("brand", ""),
                            line.get("unit", "U"),
                            line.get("discount_rate", 0),
                            line.get("client_discount_rate", 0),
                            line.get("line_total_excl_tax", 0),
                        )
                        for line in new_lines
                    ],
                )

    def safe_numeric(self, value, default=0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        print(f"[QuoteService][update_line_from_product] Updating line from product: {product}")

        if hasattr(document, "data") and isinstance(document.data, dict):
            document_dict = document.data
        else:
            document_dict = document

        if product.get("id"):
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM document_line WHERE id = %s LIMIT 1",
                (product.get("id"),),
            )
            if not rows:
                line = {
                    "document_id": document_dict.get("id"),
                }
            else:
                line = rows[0]
        else:
            line = {
                "document_id": document_dict.get("id"),
            }

        line["description"] = product.get("description")
        line["position"] = product.get("position")
        line["sku"] = product.get("sku")
        line["quantity"] = product.get("quantity")
        line["unit"] = product.get("unit")
        line["unit_price"] = product.get("price")
        line["unit_price_excl_tax"] = product.get("price")
        line["tax_rate"] = product.get("tax_rate", 20)
        line["discount_rate"] = product.get("discount_rate", 0)
        line["client_discount_rate"] = product.get("client_discount_rate", None)
        line["line_total_excl_tax"] = round(float(product.get("quantity", 1) or 1) * float(product.get("price", 0) or 0), 2)

    def _compute_document_totals(self, lines: list) -> Dict[str, float]:
        total_excl = 0.0
        total_tax = 0.0

        for line in lines:
            try:
                qty = float(line.get("quantity", 1) or 1)
            except Exception:
                qty = 1.0

            try:
                unit_price = float(line.get("unit_price_excl_tax", 0) or 0)
            except Exception:
                unit_price = 0.0

            try:
                tax_rate = float(line.get("tax_rate", 20) or 20)
            except Exception:
                tax_rate = 20.0

            client_discount_rate = 0.0
            if line.get("client_discount_rate"):
                try:
                    client_discount_rate = float(line.get("client_discount_rate")) / 100.0
                except Exception:
                    pass

            line_total = qty * unit_price * (1.0 - client_discount_rate)
            total_excl += line_total
            total_tax += line_total * (tax_rate / 100.0)

        total_excl = round(total_excl, 2)
        total_tax = round(total_tax, 2)
        total_incl = round(total_excl + total_tax, 2)

        return {
            "total_excl_tax": total_excl,
            "total_tax": total_tax,
            "total_incl_tax": total_incl,
        }

    def _compute_totals(self, rfp_data: Dict) -> Dict[str, float]:
        return self.opportunity_repository._compute_totals(rfp_data)

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

        try:
            db_handler = self._get_db_handler()
            doc_rows = db_handler.execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (document_id,),
            )
            document = doc_rows[0] if doc_rows else None
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "PDF generation is only supported for quotes"}

            opportunity_id = document.get("opportunity_id")
            account = {}
            if opportunity_id:
                opp_rows = db_handler.execute_dict_query(
                    "SELECT * FROM opportunity WHERE id = %s LIMIT 1",
                    (opportunity_id,),
                )
                if opp_rows:
                    account_id = opp_rows[0].get("account_id")
                    if account_id:
                        acc_rows = db_handler.execute_dict_query(
                            "SELECT * FROM account WHERE id = %s LIMIT 1",
                            (account_id,),
                        )
                        if acc_rows:
                            account = acc_rows[0]

            lines = db_handler.execute_dict_query(
                "SELECT * FROM document_line WHERE document_id = %s ORDER BY position",
                (document_id,),
            )

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

            db_handler.execute_update(
                """
                UPDATE document
                SET storage_key = %s,
                    total_excl_tax = %s,
                    total_tax = %s,
                    total_incl_tax = %s
                WHERE id = %s
                """,
                (
                    update_payload["storage_key"],
                    update_payload["total_excl_tax"],
                    update_payload["total_tax"],
                    update_payload["total_incl_tax"],
                    document_id,
                ),
            )

            return {"status": "ok", "pdf_filename": pdf_filename}
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Error generating PDF: {str(exc)}",
            }

    def handle_generate_quote_pdf_from_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        _ = user_id

        try:
            quote_rows = self._get_db_handler().execute_dict_query(
                """
                SELECT id
                FROM document
                WHERE opportunity_id = %s
                  AND type = 'QUOTE'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (opportunity_id,),
            )

            if not quote_rows:
                return {"status": "error", "message": f"No quote found for opportunity {opportunity_id}"}

            document_id = quote_rows[0].get("id")
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
