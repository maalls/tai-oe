"""RFQ-related request handlers."""

import uuid
from typing import Dict
from pathlib import Path
import time

from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.supabase.supabase_client import get_supabase_service
from src.text.reader import extract_company_from_text
from src.text.reader import extract_rfp_from_text
from src.text.rfp_source_picker import pick_best_rfp_source


class RfqHandlers:
    """Handle RFQ generation flows."""

    def __init__(
        self,
        service_factory: ServiceFactory = None,
        email_repository: EmailRepository = None,
        opportunity_repository: OpportunityRepository = None,
        supabase=None,
    ):
        self.service_factory = service_factory or ServiceFactory()
        self.email_repository = email_repository or EmailRepository()
        self.opportunity_repository = opportunity_repository or OpportunityRepository()
        self.supabase = supabase or get_supabase_service()

    def _load_email_content(self, message_id: str) -> str:
        """Load email content, preferring the DDD service and falling back to legacy preview data."""
        email_service = self.service_factory.create_email_service()
        email = email_service.get_email(message_id)
        if email.body:
            return email.body

        legacy_email = self.email_repository.db_handler.get_email(message_id)
        if legacy_email:
            return legacy_email.get("body_full") or legacy_email.get("body_preview") or ""

        return ""

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        """Generate an RFQ draft from raw text or a stored email."""
        try:
            content = text or ""

            if not content and message_id:
                try:
                    content = self._load_email_content(message_id)
                except Exception as exc:
                    print(f"[RfqHandlers] Warning: could not load email body for RFQ generation: {exc}")

            if not content:
                return {
                    "status": "error",
                    "message": "No text provided and unable to load email body",
                }

            draft = extract_rfp_from_text(content, timeout_seconds=300)
            rfq_id = str(uuid.uuid4())

            return {
                "status": "ok",
                "rfq_id": rfq_id,
                "type": "RFQ",
                "draft": draft,
            }
        except Exception as exc:
            print(f"[RfqHandlers] Error generating RFQ: {exc}")
            return {
                "status": "error",
                "message": f"Error generating RFQ: {str(exc)}",
            }

    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> Dict:
        """Create an opportunity and source document from RFP form input."""
        try:
            form_data, error = self.get_form(body, content_type)
            if error:
                return error

            message_text = str(form_data.get("message", "") or form_data.get("text", "") or "")
            uploaded_file = form_data.get("file")

            if not message_text.strip() and not uploaded_file:
                return {"status": "error", "message": "Message text or attachment is required"}

            rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(message_text)

            try:
                company_data = extract_company_from_text(self.email_repository._clean_email_body(message_text))
                if isinstance(company_data, dict) and company_data:
                    rfp_data["contact"] = company_data
            except Exception as exc:
                print(f"[RfqHandlers] Warning: Failed to extract company data: {exc}")

            opportunity_name = rfp_data.get("title") or "Message from User Form "
            account_name = rfp_data.get("contact", {}).get("company_name") if isinstance(rfp_data.get("contact"), dict) else None

            if not account_name:
                contact_data = rfp_data.get("contact", {})
                account_name = contact_data.get("company_name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = contact_data.get("name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = "Unknown Company"

            account_id = None
            try:
                account_response = self.supabase.table("account").select("id").eq("name", account_name).limit(1).execute()
                if account_response.data and len(account_response.data) > 0:
                    account_id = account_response.data[0]["id"]

                if not account_id:
                    contact_email = rfp_data.get("contact", {}).get("email") if isinstance(rfp_data.get("contact"), dict) else None
                    if contact_email:
                        contact_response = self.supabase.table("contact").select("id,account_id").eq("email", contact_email).limit(1).execute()
                        if contact_response.data and len(contact_response.data) > 0:
                            account_id = contact_response.data[0]["account_id"]
                            ar = self.supabase.table("account").select("id, name").eq("id", account_id).limit(1).execute()
                            if not ar.data or len(ar.data) == 0:
                                raise Exception("Account not found by ID from contact ID " + str(contact_response.data[0].get("id")))

                if not account_id:
                    new_account = self.supabase.table("account").insert({"name": account_name}).execute()
                    if new_account.data:
                        account_id = new_account.data[0]["id"]
            except Exception as exc:
                print(f"[RfqHandlers] Error with account: {exc}")
                raise

            if not account_id:
                return {"status": "error", "message": "Failed to create or find account"}

            opportunity_data = {
                "owner_user_id": user_id,
                "name": opportunity_name,
                "stage": "RFP_IN_PROGRESS",
                "status": "OPEN",
                "source": "rfp_upload",
                "account_id": account_id,
            }
            opp_result = self.supabase.table("opportunity").insert(opportunity_data).execute()
            if not opp_result.data:
                return {"status": "error", "message": "Failed to create opportunity"}

            opportunity_id = opp_result.data[0]["id"]

            storage_dir = self._get_storage_dir("rfp_upload")
            storage_dir.mkdir(parents=True, exist_ok=True)

            timestamp = int(time.time())
            text_filename = f"{timestamp}_message.txt"
            text_file_path = storage_dir / text_filename
            text_file_path.write_text(message_text, encoding="utf-8")

            doc_data = {
                "opportunity_id": opportunity_id,
                "type": "RFP",
                "status": "RECEIVED",
                "title": opportunity_name,
                "currency": "EUR",
                "channel": "OTHER",
                "storage_key": text_filename,
                "created_by": user_id,
            }
            doc_result = self.supabase.table("document").insert(doc_data).execute()
            if not doc_result.data:
                return {"status": "error", "message": "Failed to create document"}

            document_id = doc_result.data[0]["id"]

            if uploaded_file and isinstance(uploaded_file, dict):
                filename = uploaded_file.get("filename")
                file_content = uploaded_file.get("content")
                if filename and file_content:
                    try:
                        safe_filename = f"{timestamp}_attachment_{filename}"
                        file_path = storage_dir / safe_filename
                        file_path.write_bytes(file_content)
                        attachment_doc_data = {
                            "opportunity_id": opportunity_id,
                            "type": "ATTACHMENT",
                            "status": "RECEIVED",
                            "title": f"Attachment: {filename}",
                            "currency": "EUR",
                            "channel": "OTHER",
                            "storage_key": safe_filename,
                            "created_by": user_id,
                        }
                        self.supabase.table("document").insert(attachment_doc_data).execute()
                    except Exception as exc:
                        print(f"[RfqHandlers] Failed to save attachment: {exc}")

            self.supabase.table("opportunity").update({"source_reference_id": document_id}).eq("id", opportunity_id).execute()

            contact_data = rfp_data.get("contact", {})
            if isinstance(contact_data, dict) and contact_data.get("email"):
                try:
                    existing_contact = self.supabase.table("contact").select("id").eq("email", contact_data["email"]).eq("account_id", account_id).limit(1).execute()
                    contact_id = None
                    if existing_contact.data and len(existing_contact.data) > 0:
                        contact_id = existing_contact.data[0]["id"]
                    else:
                        new_contact_data = {
                            "account_id": account_id,
                            "name": contact_data.get("name") or contact_data.get("email"),
                            "email": contact_data["email"],
                            "phone": contact_data.get("phone"),
                        }
                        contact_result = self.supabase.table("contact").insert(new_contact_data).execute()
                        if contact_result.data:
                            contact_id = contact_result.data[0]["id"]

                    if contact_id:
                        participant_data = {
                            "opportunity_id": opportunity_id,
                            "contact_id": contact_id,
                            "role": "BUYER",
                        }
                        self.supabase.table("opportunity_participant").insert(participant_data).execute()
                except Exception as exc:
                    print(f"[RfqHandlers] Warning: Failed to create contact/participant: {exc}")

            return {
                "status": "ok",
                "opportunity": {
                    "id": opportunity_id,
                    "name": opportunity_name,
                    "stage": "RFP_IN_PROGRESS",
                    "document_id": document_id,
                },
                "extracted_rfp": rfp_data,
            }
        except Exception as exc:
            print(f"[RfqHandlers] Error creating opportunity from RFP: {exc}")
            return {"status": "error", "message": f"Error: {str(exc)}"}

    def handle_create_rfq_source_from_html_body(
        self,
        opportunity_id: str,
        body: bytes,
        content_type: str,
        user_id: str = None,
    ) -> Dict:
        """Create an RFQ source document from HTML/body input and optionally generate a quote."""
        form_data, error = self.get_form(body, content_type)
        if error:
            return error

        message_text = str(form_data.get("message", "") or form_data.get("text", "") or "")
        uploaded_file = form_data.get("file")
        provided_opportunity_name = str(form_data.get("opportunity_name", "") or "")

        if not message_text.strip() and not uploaded_file:
            return {"status": "error", "message": "Message text or attachment is required"}
        if not message_text.strip() and uploaded_file:
            message_text = ""

        rfp_data = {"products": [], "contact": {}}
        message_is_placeholder = message_text.strip() == ""
        if message_text.strip() and not message_is_placeholder:
            rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(message_text)
            company_data = extract_company_from_text(self.email_repository._clean_email_body(message_text))
            if isinstance(company_data, dict) and company_data:
                rfp_data["contact"] = company_data

        opportunity_name = provided_opportunity_name or rfp_data.get("title") or "RFP from Source Page"
        account_name = rfp_data.get("contact", {}).get("company_name") if isinstance(rfp_data.get("contact"), dict) else None

        if opportunity_id == "new":
            account_id = None
            if not account_name:
                contact_data = rfp_data.get("contact", {})
                account_name = contact_data.get("company_name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = contact_data.get("name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = "Unknown Company"

            try:
                account_response = self.supabase.table("account").select("id").eq("name", account_name).limit(1).execute()
                if account_response.data and len(account_response.data) > 0:
                    account_id = account_response.data[0]["id"]

                if not account_id:
                    contact_email = rfp_data.get("contact", {}).get("email") if isinstance(rfp_data.get("contact"), dict) else None
                    if contact_email:
                        contact_response = self.supabase.table("contact").select("account_id").eq("email", contact_email).limit(1).execute()
                        if contact_response.data and len(contact_response.data) > 0:
                            account_id = contact_response.data[0]["account_id"]

                if not account_id:
                    new_account = self.supabase.table("account").insert({"name": account_name}).execute()
                    if new_account.data:
                        account_id = new_account.data[0]["id"]
            except Exception as exc:
                print(f"[RfqHandlers] Error with account: {exc}")
                raise

            if not account_id:
                return {"status": "error", "message": "Failed to create or find account"}

            opportunity_data = {
                "owner_user_id": user_id,
                "name": opportunity_name,
                "stage": "RFP_IN_PROGRESS",
                "status": "OPEN",
                "source": "user_form",
                "account_id": account_id,
            }
            opp_result = self.supabase.table("opportunity").insert(opportunity_data).execute()
            if not opp_result.data:
                return {"status": "error", "message": "Failed to create opportunity"}
            opportunity_id = opp_result.data[0]["id"]

        storage_dir = self._get_storage_dir("rfp_upload")
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())

        text_filename = f"{timestamp}_message.txt"
        text_file_path = storage_dir / text_filename
        text_file_path.write_text(message_text, encoding="utf-8")

        doc_data = {
            "opportunity_id": opportunity_id,
            "type": "RFP",
            "status": "RECEIVED",
            "title": opportunity_name,
            "currency": "EUR",
            "channel": "OTHER",
            "storage_key": text_filename,
            "created_by": user_id,
        }
        doc_result = self.supabase.table("document").insert(doc_data).execute()
        if not doc_result.data:
            return {"status": "error", "message": "Failed to create document"}
        document_id = doc_result.data[0]["id"]

        attachment_doc_id = None
        attachment_file_path = None
        attachment_content_type = None
        if uploaded_file and isinstance(uploaded_file, dict):
            filename = uploaded_file.get("filename")
            file_content = uploaded_file.get("content")
            attachment_content_type = uploaded_file.get("content_type")
            if filename and file_content:
                try:
                    safe_filename = f"{timestamp}_attachment_{filename}"
                    file_path = storage_dir / safe_filename
                    file_path.write_bytes(file_content)
                    attachment_file_path = file_path
                    attachment_doc_data = {
                        "opportunity_id": opportunity_id,
                        "type": "ATTACHMENT",
                        "status": "RECEIVED",
                        "title": f"Attachment: {filename}",
                        "currency": "EUR",
                        "channel": "OTHER",
                        "storage_key": safe_filename,
                        "created_by": user_id,
                    }
                    attachment_result = self.supabase.table("document").insert(attachment_doc_data).execute()
                    if attachment_result.data:
                        attachment_doc_id = attachment_result.data[0]["id"]
                except Exception as exc:
                    print(f"[RfqHandlers] Failed to save attachment: {exc}")

        self.supabase.table("opportunity").update({"source_reference_id": document_id, "source": "rfp_upload"}).eq("id", opportunity_id).execute()

        contact_data = rfp_data.get("contact", {})
        if isinstance(contact_data, dict) and contact_data.get("email"):
            try:
                opp_response = self.supabase.table("opportunity").select("account_id").eq("id", opportunity_id).single().execute()
                if opp_response.data:
                    account_id = opp_response.data["account_id"]
                    existing_contact = self.supabase.table("contact").select("id").eq("email", contact_data["email"]).eq("account_id", account_id).limit(1).execute()
                    contact_id = None
                    if existing_contact.data and len(existing_contact.data) > 0:
                        contact_id = existing_contact.data[0]["id"]
                    else:
                        new_contact_data = {
                            "account_id": account_id,
                            "name": contact_data.get("name") or contact_data.get("email"),
                            "email": contact_data["email"],
                            "phone": contact_data.get("phone"),
                        }
                        contact_result = self.supabase.table("contact").insert(new_contact_data).execute()
                        if contact_result.data:
                            contact_id = contact_result.data[0]["id"]
                    if contact_id:
                        participant_data = {
                            "opportunity_id": opportunity_id,
                            "contact_id": contact_id,
                            "role": "BUYER",
                        }
                        self.supabase.table("opportunity_participant").insert(participant_data).execute()
            except Exception as exc:
                print(f"[RfqHandlers] Warning: Failed to create contact/participant: {exc}")

        pdf_candidates = []
        if attachment_file_path and (attachment_content_type or "").lower().startswith("application/pdf"):
            pdf_candidates.append(
                {
                    "id": attachment_doc_id,
                    "filename": uploaded_file.get("filename") if isinstance(uploaded_file, dict) else None,
                    "path": attachment_file_path,
                }
            )

        picker_text = "" if message_is_placeholder else message_text
        selection = pick_best_rfp_source(picker_text, pdf_candidates)
        selected_content = selection.get("content") or ("" if message_is_placeholder else message_text)
        pre_extracted = selection.get("extracted_data")
        if pre_extracted is None and (rfp_data.get("products") or rfp_data.get("contact") or rfp_data.get("title")):
            pre_extracted = rfp_data

        if selected_content:
            quote_result = self.opportunity_repository.handle_generate_quote_with_content(
                opportunity_id=opportunity_id,
                content=selected_content,
                user_id=user_id,
                pre_extracted_data=pre_extracted,
            )
        else:
            quote_result = self.opportunity_repository.handle_generate_quote_for_opportunity(
                opportunity_id=opportunity_id,
                user_id=user_id,
            )

        return {
            "status": "ok",
            "message": "RFQ source created successfully",
            "opportunity_id": opportunity_id,
            "document_id": document_id,
            "attachment_doc_id": attachment_doc_id,
            "quote": quote_result,
            "opportunity": {"id": opportunity_id},
        }

    def get_form(self, body: bytes, content_type: str):
        boundary = self._extract_boundary(content_type)
        if not boundary:
            return None, {"status": "error", "message": "Invalid content type"}
        return self._parse_multipart(body, boundary), None

    @staticmethod
    def _extract_boundary(content_type: str):
        if "boundary=" not in content_type:
            return None
        boundary = content_type.split("boundary=")[1]
        return boundary.strip('"\'')

    @staticmethod
    def _parse_multipart(body: bytes, boundary: str) -> Dict:
        form_data = {}
        parts = body.split(f"--{boundary}".encode())
        for part in parts[1:-1]:
            if not part.strip():
                continue
            try:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    header_end = part.find(b"\n\n")
                    if header_end == -1:
                        continue
                    content_start = header_end + 2
                else:
                    content_start = header_end + 4

                headers = part[:header_end].decode("utf-8", errors="ignore")
                content = part[content_start:]
                if content.endswith(b"\r\n"):
                    content = content[:-2]
                elif content.endswith(b"\n"):
                    content = content[:-1]

                if "Content-Disposition" in headers:
                    disp_line = [h for h in headers.split("\n") if "Content-Disposition" in h][0]
                    if 'name="' in disp_line:
                        name_start = disp_line.find('name="') + 6
                        name_end = disp_line.find('"', name_start)
                        name = disp_line[name_start:name_end]
                        if "filename=" in disp_line:
                            filename_start = disp_line.find('filename="') + 10
                            filename_end = disp_line.find('"', filename_start)
                            filename = disp_line[filename_start:filename_end]
                            content_type = "application/octet-stream"
                            for header_line in headers.split("\n"):
                                if "Content-Type:" in header_line:
                                    content_type = header_line.split("Content-Type:")[1].strip()
                            form_data[name] = {
                                "filename": filename,
                                "content": content,
                                "content_type": content_type,
                                "size": len(content),
                            }
                        else:
                            form_data[name] = content.decode("utf-8", errors="ignore")
            except Exception as exc:
                print(f"[RfqHandlers] Error parsing part: {exc}")
                continue
        return form_data

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