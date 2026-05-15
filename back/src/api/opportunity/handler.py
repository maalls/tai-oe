"""Opportunity-related request handlers (migrated from rfq/business split)."""

from src.api.routes.server_auth_helpers import require_auth, require_auth_user_id
from src.api.routes.server_body_helpers import read_body, read_json, read_json_or_error
from src.api.routes.server_status_helpers import status_from_result
from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text
from src.lib.extractors.text_reader import extract_rfp_from_text
from src.lib.storage_paths import get_storage_dir
from pathlib import Path
import uuid
import time



class OpportunityHandlers:

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        return get_storage_dir(source)

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


def handle_opportunities_create_from_email_post(handler):
    """Handle /api/opportunities/create-from-email POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    payload = read_json(handler, default={})

    message_id = payload.get('message_id')
    if not message_id:
        return handler.json({"error": "Missing message_id parameter"}, 400)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_from_email(message_id=message_id, user_id=user_id)
    print(f"[RAG] Create opportunity result: {result.get('status')}, {result}")
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunities_create_manual_post(handler):
    """Handle /api/opportunities/create-manual POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    payload = read_json(handler, default={})

    name = payload.get('name')
    if not name:
        return handler.json({"status": "error", "message": "Missing name parameter"}, 400)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_manual(user_id=user_id, name=name)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunities_create_from_rfp_post(handler):
    """Handle /api/opportunities/create-from-rfp POST endpoint."""
    body = read_body(handler)
    content_type = handler.headers.get('Content-Type', '')

    auth_header = handler.headers.get('Authorization', '')
    print(f"[RAG] Auth header present: {bool(auth_header)}, header: {auth_header[:50] if auth_header else 'None'}")
    user_data = require_auth(handler, auth_header=auth_header)
    print(f"[RAG] Token valid: {bool(user_data)}, user_data: {user_data}")
    if user_data is None:
        print(f"[RAG] Authorization failed for token: {auth_header[:50] if auth_header else 'None'}")
        return None

    user_id = user_data.get('id') if user_data else None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_from_rfp(body=body, content_type=content_type, user_id=user_id)
    print(f"[RAG] Create opportunity from RFP result: {result.get('status')}")
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunity_rfq_generate_post(handler, opp_match):
    """Handle /api/opportunity/{id}/rfq/generate POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    opportunity_id = opp_match.group(1)
    request_handlers = handler.get_request_handlers()
    print(f"[RAG] Generating quote for opportunity {opportunity_id} by user {user_id}")
    result = request_handlers.handle_generate_quote_for_opportunity(
        opportunity_id=opportunity_id,
        user_id=user_id,
    )
    print('result:', result)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunity_rfq_create_from_text_post(handler, opp_rfq_create_match):
    """Handle /api/opportunity/{id}/rfq/create-from-text POST endpoint."""
    body = read_body(handler)
    content_type = handler.headers.get('Content-Type', '')

    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    request_handlers = handler.get_request_handlers()
    opportunity_id = opp_rfq_create_match.group(1)

    if opportunity_id == 'new':
        result = request_handlers.handle_create_opportunity_from_rfp(
            body=body,
            content_type=content_type,
            user_id=user_id,
        )
        if result.get('status') == 'ok':
            opportunity = result.get('opportunity', {})
            opportunity_id = opportunity.get('id')
            print(f"[ServerPostUtilityHandlers] Generating quote for opportunity {opportunity_id} by user")
            request_handlers.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)
    else:
        result = request_handlers.handle_create_rfq_source_from_html_body(
            opportunity_id=opportunity_id,
            body=body,
            content_type=content_type,
            user_id=user_id,
        )

    status = status_from_result(result)
    return handler.json(result, status)


def handle_send_quote_for_opportunity_post(handler, send_quote_match):
    """Handle /api/opportunity/{id}/send-quote POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    opportunity_id = send_quote_match.group(1)

    payload = read_json_or_error(handler)
    if payload is None:
        return None

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_send_quote_for_opportunity(
        opportunity_id=opportunity_id,
        payload=payload,
        user_id=user_id,
    )
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunity_delete(handler, opportunity_delete_match):
    """Handle DELETE /api/opportunities/{ids}."""
    import sys

    print("[RAG] DELETE /api/opportunities matched, processing deletion", file=sys.stderr)
    user_data = require_auth(handler)
    if user_data is None:
        print("[RAG] DELETE - Auth failed", file=sys.stderr)
        return None

    user_id = user_data.get('id') if user_data else None
    opportunity_ids = opportunity_delete_match.group(1)
    print(f"[RAG] DELETE opportunity(ies) {opportunity_ids} for user {user_id}", file=sys.stderr)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_delete_opportunity(opportunity_ids=opportunity_ids, user_id=user_id)
    status = status_from_result(result)
    print(f"[RAG] DELETE result: {result}", file=sys.stderr)
    return handler.json(result, status)


def handle_opportunities_search_get(handler, qs, request_handlers):
    """Handle /api/opportunities/search GET endpoint."""
    source_reference_id = qs.get('source_reference_id', [None])[0]
    name = qs.get('name', [None])[0]

    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None

    result = request_handlers.handle_search_opportunities(
        user_id=user_id,
        source_reference_id=source_reference_id,
        name=name,
    )
    status = status_from_result(result)
    return handler.json(result, status)
