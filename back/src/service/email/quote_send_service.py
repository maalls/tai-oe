"""Service for quote email sending flows."""

import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service


class QuoteSendService:
    """Encapsulates quote send workflows previously handled in API layer."""

    def __init__(
        self,
        send_email: Callable[..., Dict],
        storage_path_resolver: Callable[[str, str], Path],
        path_cls=Path,
        supabase_factory: Callable[[], object] = get_supabase_service,
        now_provider: Callable[[], datetime] = None,
    ):
        self._send_email = send_email
        self._storage_path_resolver = storage_path_resolver
        self._path_cls = path_cls
        self._supabase_factory = supabase_factory
        self._now_provider = now_provider or datetime.now

    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        """Send a quote PDF by email using the legacy quote-send contract."""
        _ = content_type
        try:
            payload = json.loads(body.decode("utf-8"))

            pdf_filename = payload.get("pdf_filename")
            email = payload.get("email")
            email_body = payload.get("body", "Hi, here is the quote")

            if not pdf_filename:
                return {
                    "status": "error",
                    "message": "Missing pdf_filename",
                }

            if not email:
                return {
                    "status": "error",
                    "message": "Missing email address",
                }

            if not pdf_filename.startswith("quote_") or not pdf_filename.endswith(".pdf"):
                return {
                    "status": "error",
                    "message": "Invalid PDF filename format",
                }

            assets_dir = self._path_cls(__file__).parent.parent.parent / "var" / "assets"
            pdf_path = assets_dir / pdf_filename
            if not pdf_path.exists():
                return {
                    "status": "error",
                    "message": f"Quote PDF not found: {pdf_filename}",
                }

            result = self._send_email(
                to=email,
                subject="Your Quote",
                body=email_body,
                attachment_path=str(pdf_path),
            )

            if result.get("status") == "ok":
                print(f"[QuoteSendService] Quote email sent successfully to {email}")
                return {
                    "status": "ok",
                    "message": "Quote emailed successfully",
                    "email": email,
                    "message_id": result.get("message_id"),
                }

            return result
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in request body",
            }
        except Exception as exc:
            print(f"[QuoteSendService] Error sending quote email: {exc}")
            return {
                "status": "error",
                "message": f"Error sending email: {str(exc)}",
            }

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Send quote email with optional PDF and persist send side effects."""
        try:
            to_emails = payload.get("to", [])
            cc_emails = payload.get("cc", [])
            subject = payload.get("subject", "")
            body = payload.get("body", "")
            pdf_filename = payload.get("storage_key", "")

            if not to_emails or not isinstance(to_emails, list):
                return {"status": "error", "message": "At least one 'to' email is required"}
            if not subject:
                return {"status": "error", "message": "Email subject is required"}
            if not body:
                return {"status": "error", "message": "Email body is required"}

            pdf_path = None
            if pdf_filename:
                pdf_path = self._storage_path_resolver("quote", pdf_filename)
                if not pdf_path.exists():
                    legacy_assets_dir = self._path_cls(__file__).parent.parent.parent / "var" / "assets"
                    legacy_pdf_path = legacy_assets_dir / pdf_filename
                    if legacy_pdf_path.exists():
                        pdf_path = legacy_pdf_path
                    else:
                        return {"status": "error", "message": f"PDF file not found: {pdf_filename}"}

            to_recipients = ", ".join(to_emails)
            cc_recipients = ", ".join(cc_emails) if cc_emails else None

            result = self._send_email(
                to=to_recipients,
                cc=cc_recipients,
                subject=subject,
                body=body,
                attachment_path=str(pdf_path) if pdf_path else None,
                user_id=user_id,
            )

            if result.get("status") not in ("success", "ok"):
                if isinstance(result, dict) and result.get("status") == "error":
                    return result
                return {
                    "status": "error",
                    "message": result.get("message", "Failed to send email") if isinstance(result, dict) else str(result),
                }

            supabase = self._supabase_factory()
            quote_id = payload.get("quote_id")
            if not quote_id:
                raise ValueError("quote_id not provided in payload")

            now_iso = self._now_provider().isoformat()

            update_payload = {
                "status": "SENT",
                "channel": "EMAIL",
                "source_message_id": result.get("message_id"),
                "issued_at": now_iso,
            }
            sent_doc_resp = supabase.table("document").update(update_payload).eq("id", quote_id).execute()
            if getattr(sent_doc_resp, "error", None):
                raise RuntimeError(f"Failed to update quote document: {sent_doc_resp.error}")
            if not sent_doc_resp.data:
                raise RuntimeError(f"Update executed but no rows affected for quote {quote_id}")

            sent_email_data = {
                "document_id": quote_id,
                "opportunity_id": opportunity_id,
                "from_email": "maalls@gmail.com",
                "to_emails": to_emails,
                "cc_emails": cc_emails if cc_emails else [],
                "subject": subject,
                "body": body,
                "provider": result.get("provider") or "gmail",
                "provider_message_id": result.get("message_id"),
                "status": "sent",
                "sent_at": now_iso,
                "attachment_names": [pdf_filename] if pdf_filename else [],
            }
            insert_result = supabase.table("sent_email").insert(sent_email_data).execute()
            if getattr(insert_result, "error", None):
                raise RuntimeError(f"Failed to save sent_email record: {insert_result.error}")
            if not insert_result.data:
                raise RuntimeError("Sent email insert returned no data")

            update_resp = supabase.table("opportunity").update(
                {
                    "stage": "OFFER_SENT",
                    "updated_at": now_iso,
                }
            ).eq("id", opportunity_id).execute()
            if getattr(update_resp, "error", None):
                raise RuntimeError(f"Failed to update opportunity stage: {update_resp.error}")
            if not update_resp.data:
                raise RuntimeError(f"Opportunity stage update returned no data for {opportunity_id}")

            return {
                "status": "ok",
                "message": "Quote email sent successfully",
                "message_id": result.get("message_id"),
                "recipients": to_recipients,
            }
        except Exception as exc:
            print(f"[QuoteSendService] Error sending quote email: {exc}")
            return {
                "status": "error",
                "message": f"Failed to send email: {str(exc)}",
            }
