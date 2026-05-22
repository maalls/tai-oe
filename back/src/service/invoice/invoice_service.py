"""Invoice service for FastAPI transport."""

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict
import uuid

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.lib.storage_paths import get_storage_dir


class InvoiceService:
    """Handle invoice generation/pdf/send flows for FastAPI."""

    def __init__(
        self,
        db_handler: DatabaseHandler = None,
        send_email_with_attachments: Callable = None,
        storage_path_resolver: Callable = None,
    ):
        self.db_handler = db_handler
        self.send_email_with_attachments = send_email_with_attachments
        self.storage_path_resolver = storage_path_resolver

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        try:
            db_handler = self._get_db_handler()
            quote_rows = db_handler.execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (quote_id,),
            )

            if not quote_rows:
                quote_rows = db_handler.execute_dict_query(
                    """
                    SELECT *
                    FROM document
                    WHERE opportunity_id = %s
                      AND type = 'QUOTE'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (quote_id,),
                )

            if not quote_rows:
                return {"status": "error", "message": f"Quote not found for {quote_id}"}

            quote = quote_rows[0]
            if quote.get("type") != "QUOTE":
                return {"status": "error", "message": "Document must be a QUOTE"}

            quote_document_id = quote.get("id")

            existing_rows = db_handler.execute_dict_query(
                """
                SELECT id
                FROM document
                WHERE parent_document_id = %s
                  AND type = 'INVOICE'
                LIMIT 1
                """,
                (quote_document_id,),
            )
            if existing_rows:
                return {"status": "error", "message": "Invoice already exists for this quote"}

            lines = db_handler.execute_dict_query(
                """
                SELECT *
                FROM document_line
                WHERE document_id = %s
                ORDER BY position
                """,
                (quote_document_id,),
            )

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

            inv_rows = db_handler.execute_dict_query(
                """
                INSERT INTO document (
                    type,
                    status,
                    opportunity_id,
                    parent_document_id,
                    title,
                    external_ref,
                    currency,
                    total_excl_tax,
                    total_tax,
                    total_incl_tax,
                    issued_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    invoice_data["type"],
                    invoice_data["status"],
                    invoice_data["opportunity_id"],
                    invoice_data["parent_document_id"],
                    invoice_data["title"],
                    invoice_data["external_ref"],
                    invoice_data["currency"],
                    invoice_data["total_excl_tax"],
                    invoice_data["total_tax"],
                    invoice_data["total_incl_tax"],
                    invoice_data["issued_at"],
                ),
            )
            if not inv_rows:
                return {"status": "error", "message": "Failed to create invoice"}

            invoice_id = inv_rows[0]["id"]

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

            for line in invoice_lines:
                db_handler.execute_update(
                    """
                    INSERT INTO document_line (
                        document_id,
                        position,
                        sku,
                        brand,
                        description,
                        quantity,
                        unit,
                        unit_price_excl_tax,
                        tax_rate,
                        line_total_excl_tax
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        line.get("document_id"),
                        line.get("position"),
                        line.get("sku"),
                        line.get("brand"),
                        line.get("description"),
                        line.get("quantity"),
                        line.get("unit"),
                        line.get("unit_price_excl_tax"),
                        line.get("tax_rate"),
                        line.get("line_total_excl_tax"),
                    ),
                )

            storage_key = None
            try:
                pdf_result = self.handle_generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
                if pdf_result.get("status") == "ok":
                    storage_key = pdf_result.get("storage_key")
            except Exception as pdf_error:
                print(f"[InvoiceService] Warning: Error auto-generating invoice PDF: {pdf_error}")

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

        except Exception as exc:
            print(f"[InvoiceService] Error generating invoice from quote {quote_id}: {exc}")
            return {"status": "error", "message": f"Error generating invoice: {str(exc)}"}

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        return get_storage_dir(source)

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

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
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

            if document.get("type") != "INVOICE":
                return {"status": "error", "message": "PDF generation is only supported for invoices"}

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
                """
                SELECT *
                FROM document_line
                WHERE document_id = %s
                ORDER BY position
                """,
                (document_id,),
            )

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
            db_handler.execute_update(
                "UPDATE document SET storage_key = %s WHERE id = %s",
                (pdf_filename, document_id),
            )

            return {"status": "ok", "storage_key": pdf_filename}

        except Exception as exc:
            print(f"[InvoiceService] Error generating PDF for invoice {document_id}: {exc}")
            return {"status": "error", "message": f"Error generating PDF: {str(exc)}"}

    def _generate_invoice_pdf(self, invoice_data: Dict) -> str:
        storage_dir = self._get_storage_dir("invoice")
        storage_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path(__file__).resolve().parents[3] / "templates"

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

    def handle_send_invoice(self, invoice_id: str, payload: Dict, user_id: str = None) -> Dict:
        try:
            db_handler = self._get_db_handler()
            invoice_rows = db_handler.execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (invoice_id,),
            )
            if not invoice_rows:
                return {"status": "error", "message": "Invoice not found"}

            invoice = invoice_rows[0]
            if invoice.get("type") != "INVOICE":
                return {"status": "error", "message": "Document is not an invoice"}

            storage_key = invoice.get("storage_key")
            if not storage_key:
                return {"status": "error", "message": "Invoice PDF not generated yet"}

            to_emails = payload.get("to", [])
            cc_emails = payload.get("cc", [])
            subject = payload.get("subject", f"Invoice {invoice.get('external_ref', '')}")
            body = payload.get("body", "Please find attached your invoice.")

            if not to_emails or not isinstance(to_emails, list) or len(to_emails) == 0:
                return {"status": "error", "message": "At least one 'to' email is required"}
            if not subject:
                return {"status": "error", "message": "Email subject is required"}

            if self.storage_path_resolver is not None:
                invoice_path = self.storage_path_resolver("invoice", storage_key)
            else:
                invoice_path = self._get_storage_dir("invoice") / storage_key

            if not invoice_path.exists():
                assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                invoice_path = assets_dir / storage_key
                if not invoice_path.exists():
                    return {"status": "error", "message": f"Invoice PDF file not found: {storage_key}"}

            if self.send_email_with_attachments is None:
                return {"status": "error", "message": "Email sender is not configured"}

            result = self.send_email_with_attachments(
                to=to_emails,
                cc=cc_emails,
                subject=subject,
                body=body,
                attachment_paths=[str(invoice_path)],
                user_id=user_id,
            )

            if result.get("status") != "ok":
                return result

            db_handler.execute_update(
                "UPDATE document SET status = %s WHERE id = %s",
                ("SENT", invoice_id),
            )

            sent_email_data = {
                "document_id": invoice_id,
                "opportunity_id": invoice.get("opportunity_id"),
                "from_email": "maalls@gmail.com",
                "to_emails": to_emails,
                "cc_emails": cc_emails if cc_emails else [],
                "subject": subject,
                "body": body,
                "provider": "gmail",
                "provider_message_id": result.get("message_id"),
                "status": "sent",
                "sent_at": datetime.now().isoformat(),
                "attachment_names": [storage_key] if storage_key else [],
            }

            try:
                db_handler.execute_update(
                    """
                    INSERT INTO sent_email (
                        document_id,
                        opportunity_id,
                        from_email,
                        to_emails,
                        cc_emails,
                        subject,
                        body,
                        provider,
                        provider_message_id,
                        status,
                        sent_at,
                        attachment_names
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        sent_email_data["document_id"],
                        sent_email_data["opportunity_id"],
                        sent_email_data["from_email"],
                        sent_email_data["to_emails"],
                        sent_email_data["cc_emails"],
                        sent_email_data["subject"],
                        sent_email_data["body"],
                        sent_email_data["provider"],
                        sent_email_data["provider_message_id"],
                        sent_email_data["status"],
                        sent_email_data["sent_at"],
                        sent_email_data["attachment_names"],
                    ),
                )
            except Exception as exc:
                print(f"[InvoiceService] Warning: Failed to save sent_email record: {exc}")

            return {
                "status": "ok",
                "message": "Invoice sent successfully",
                "recipients": to_emails,
                "message_id": result.get("message_id"),
            }

        except Exception as exc:
            print(f"[InvoiceService] Error sending invoice {invoice_id}: {exc}")
            return {"status": "error", "message": f"Error sending invoice: {str(exc)}"}
