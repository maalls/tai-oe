"""Opportunity-related request handlers (migrated from rfq/business split)."""

from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text
from src.lib.extractors.text_reader import extract_rfp_from_text
from pathlib import Path
import uuid
import time



class OpportunityHandlers:

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None) -> dict:
        return self.opportunity_repository.handle_generate_quote_with_content(opportunity_id=opportunity_id, content=content, user_id=user_id)

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> dict:
        return self.opportunity_repository.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> dict:
        return self.opportunity_repository.create_opportunity_manual(user_id=user_id, name=name)

    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None) -> dict:
        return self.opportunity_repository.search_opportunities(user_id=user_id, source_reference_id=source_reference_id, name=name)

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None) -> dict:
        return self.opportunity_repository.delete_opportunities(opportunity_ids=opportunity_ids, user_id=user_id)

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

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> dict:
        """Generate an RFQ draft from raw text or a stored email."""
        try:
            content = text or ""

            if not content and message_id:
                try:
                    content = self._load_email_content(message_id)
                except Exception as exc:
                    print(f"[OpportunityHandlers] Warning: could not load email body for RFQ generation: {exc}")

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
            print(f"[OpportunityHandlers] Error generating RFQ: {exc}")
            return {
                "status": "error",
                "message": f"Error generating RFQ: {str(exc)}",
            }

    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> dict:
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
                print(f"[OpportunityHandlers] Warning: Failed to extract company data: {exc}")

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
                print(f"[OpportunityHandlers] Error with account: {exc}")
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
                        print(f"[OpportunityHandlers] Failed to save attachment: {exc}")

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
                    print(f"[OpportunityHandlers] Warning: Failed to create contact/participant: {exc}")

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
            print(f"[OpportunityHandlers] Error creating opportunity from RFP: {exc}")
            return {"status": "error", "message": f"Error: {str(exc)}"}
