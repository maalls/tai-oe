"""Main request handlers orchestration for the RAG server."""

from typing import Optional, Dict

from src.controller.file_handler import FileHandler
from src.controller.csv_handlers import CsvHandlers
from src.controller.database_handlers import DatabaseHandlers
from src.controller.business_handler import BusinessHandlers
from src.controller.email_handler import EmailHandlers
from src.controller.action_handlers import ActionHandlers
from src.controller.db_client import DatabaseHandler


class RequestHandlers:
    """HTTP request handlers orchestration layer."""
    
    def __init__(
        self,
        file_handler: FileHandler,
    ):
        self.file_handler = file_handler
        # Delegate to specialized handlers
        self.csv_handlers = CsvHandlers(file_handler)
        self.business_handlers = BusinessHandlers()
        self.email_handlers = EmailHandlers()
        self.action_handlers = ActionHandlers()

        try:
            db_handler = DatabaseHandler()
            self.database_handlers = DatabaseHandlers(db_handler)
        except Exception as e:
            print(f"[Rag] Warning: Could not initialize DatabaseHandler: {e}")
                    
    

    # CSV file operations
    def handle_list_files(self, qs: Dict) -> Dict:
        """Handle /api/csv/files request."""
        return self.csv_handlers.handle_list_files(qs)
    
    def handle_sources(self) -> list:
        """Handle /api/csv/sources request."""
        return self.csv_handlers.handle_sources()
    
    def handle_preview(self, qs: Dict) -> Dict:
        """Handle /api/csv/preview request."""
        return self.csv_handlers.handle_preview(qs)
    
    def handle_raw(self, qs: Dict) -> bytes:
        """Handle /api/csv/raw request."""
        return self.csv_handlers.handle_raw(qs)

    def handle_source_raw(self, qs: Dict) -> bytes:
        """Handle /api/csv/source request."""
        return self.csv_handlers.handle_source_raw(qs)
    
    # Database operations
    def handle_query(self, qs: Dict) -> Dict:
        """Handle /api/csv/query request."""
        return self.database_handlers.handle_query(qs)
    
    def handle_search(self, qs: Dict, embedding_generator) -> Dict:
        """Handle /api/csv/search request."""
        return self.database_handlers.handle_search(qs, embedding_generator)
    
    # Business operations
    def handle_rfp_upload(self, body: bytes, content_type: str) -> Dict:
        """Handle /api/rfp request."""
        return self.business_handlers.handle_rfp_upload(body, content_type)
    
    def handle_quote_submit(self, body: bytes, content_type: str) -> Dict:
        """Handle /api/quote request."""
        return self.business_handlers.handle_quote_submit(body, content_type)
    
    def handle_list_quotes(self) -> Dict:
        """Handle /api/quotes/list request."""
        return self.business_handlers.handle_list_quotes()
    
    def handle_get_quote_file(self, filename: str) -> bytes:
        """Handle /api/quotes/download request."""
        return self.business_handlers.handle_get_quote_file(filename)
    
    def handle_get_document_file(self, filename: str) -> bytes:
        """Handle /api/documents/download request."""
        return self.business_handlers.handle_get_document_file(filename)
    
    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        """Handle /api/quote/send request."""
        return self.business_handlers.handle_quote_send(body, content_type)    

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        """Handle /api/rfq/generate request."""
        return self.business_handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Handle /api/opportunity/{id}/rfq/generate request."""
        return self.business_handlers.opportunity_repository.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/quote/{id}/pdf request."""
        return self.business_handlers.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)

    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/quote/{id} delete request."""
        return self.business_handlers.handle_delete_quote_document(document_id=document_id, user_id=user_id)

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/document/{id} delete request (generic for all document types)."""
        return self.business_handlers.handle_delete_document(document_id=document_id, user_id=user_id)

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        """Handle /api/quote/{id}/invoice request."""
        return self.business_handlers.handle_generate_invoice_from_quote(quote_id=quote_id, user_id=user_id)

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/invoice/{id}/pdf request."""
        return self.business_handlers.handle_generate_invoice_pdf(document_id=document_id, user_id=user_id)

    def handle_send_invoice(self, invoice_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Handle /api/invoice/{id}/send request."""
        return self.business_handlers.handle_send_invoice(invoice_id=invoice_id, payload=payload, user_id=user_id)

    def handle_update_entity_field(self, table: str, field: str, record_id: str, value, user_id: str = None) -> Dict:
        """Handle /api/entity/{table}/{field} update request."""
        return self.business_handlers.handle_update_entity_field(table=table, field=field, record_id=record_id, value=value, user_id=user_id)

    def handle_update_line_verification(self, document_id: str, line_index: int, verification_fields: dict = None, is_ref_verified: bool = None, user_id: str = None) -> Dict:
        """Handle PATCH /api/quote/{id}/line/{idx}/verify request."""
        # Support both old single-field and new multi-field interfaces
        if verification_fields is None:
            verification_fields = {}
            if is_ref_verified is not None:
                verification_fields['is_ref_verified'] = is_ref_verified
        return self.business_handlers.handle_update_line_verification(document_id=document_id, line_index=line_index, verification_fields=verification_fields, user_id=user_id)

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        """Handle /api/opportunities/create-from-email request."""
        result = self.business_handlers.handle_create_opportunity_from_email(message_id=message_id, user_id=user_id)
        if result.get('status') == 'ok':
            opportunity = result.get('opportunity', {})
            opportunity_id = opportunity.get('id')
            print(f"[BusinessHandlers] Generating quote for opportunity {opportunity_id} by user")
            self.business_handlers.opportunity_repository.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)

        return result

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        """Handle /api/opportunities/create-manual request."""
        return self.business_handlers.opportunity_repository.create_opportunity_manual(
            user_id=user_id,
            name=name,
        )
    
    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None) -> Dict:
        """Handle /api/opportunities/search request."""
        return self.business_handlers.opportunity_repository.search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )
    
    def handle_delete_opportunity(self, opportunity_ids: str, user_id: str = None) -> Dict:
        """Handle DELETE /api/opportunities/{ids} request. Supports single or comma-separated IDs."""
        # Parse IDs - can be single ID or comma-separated list
        ids_list = [id.strip() for id in opportunity_ids.split(',') if id.strip()]
        return self.business_handlers.opportunity_repository.delete_opportunities(opportunity_ids=ids_list, user_id=user_id)
    
    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> Dict:
        """Handle /api/opportunities/create-from-rfp request."""
        return self.business_handlers.handle_create_opportunity_from_rfp(body=body, content_type=content_type, user_id=user_id)

    def handle_create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None) -> Dict:
        """Handle /api/opportunity/{id}/rfq/create-from-text request."""
        result = self.business_handlers.handle_create_rfq_source_from_html_body(
            opportunity_id=opportunity_id,
            body=body,
            content_type=content_type,
            user_id=user_id,
        )
        if result.get('status') != 'ok':
            print(f"[BusinessHandlers] Could not create RFQ source from text: {result}")
        return result

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str) -> Dict:
        """Handle /api/chat/attachments upload request."""
        return self.business_handlers.handle_chat_attachment_upload(
            body=body,
            content_type=content_type,
            user_id=user_id,
            opportunity_id=opportunity_id,
        )

    def handle_gmail_authorize(self, redirect_url: str = None) -> Dict:
        """Handle /api/gmail/authorize request."""
        return self.email_handlers.handle_gmail_authorize(redirect_url)
    
    def handle_gmail_list_messages(self, max_results: int = 20, user_id: str = None, save_to_db: bool = True, force: bool = False) -> Dict:
        """Handle /api/gmail/messages request."""
        return self.email_handlers.handle_gmail_list_messages(max_results, user_id, save_to_db, force)
    
    def handle_get_message_body(self, message_id: str, user_id: str = None) -> Dict:
        """Handle /api/gmail/message/{id} request."""
        return self.email_handlers.handle_get_message_body(message_id, user_id)

    def handle_gmail_status(self, user_id: str = None) -> Dict:
        """Handle Gmail status"""
        return self.email_handlers.get_gmail_status(user_id=user_id)

    def handle_gmail_revoke(self, user_id: str = None) -> Dict:
        """Handle Gmail revoke"""
        return self.email_handlers.revoke_gmail(user_id=user_id)

    def handle_gmail_profile(self, user_id: str = None) -> Dict:
        """Handle Gmail profile"""
        return self.email_handlers.get_gmail_profile(user_id=user_id)

    def handle_imap_status(self, user_id: str) -> Dict:
        """Handle IMAP status."""
        return self.email_handlers.get_imap_status(user_id)

    def handle_imap_config(self, user_id: str) -> Dict:
        """Handle IMAP config read."""
        return self.email_handlers.get_imap_config(user_id)

    def handle_imap_config_save(self, user_id: str, payload: Dict) -> Dict:
        """Handle IMAP config save."""
        return self.email_handlers.save_imap_config(user_id, payload)

    def handle_imap_config_delete(self, user_id: str) -> Dict:
        """Handle IMAP config delete."""
        return self.email_handlers.clear_imap_config(user_id)

    def handle_imap_test(self, user_id: str) -> Dict:
        """Handle IMAP connection test."""
        return self.email_handlers.test_imap_connection(user_id)

    def handle_gmail_oauth_start(self, redirect_url: str = None, user_id: str = None) -> Dict:
        """Handle Gmail OAuth start"""
        return self.email_handlers.get_gmail_oauth_url(redirect_url, user_id=user_id)

    def handle_gmail_oauth_callback(self, code: str, state: str = None) -> Dict:
        """Handle Gmail OAuth callback"""
        return self.email_handlers.handle_gmail_oauth_callback(code, state)

    def handle_email_attachment_download(self, attachment_id: str, user_id: str = None):
        """Handle /api/email-attachment/{id}/download request."""
        return self.email_handlers.handle_email_attachment_download(attachment_id, user_id)

    def handle_email_attachment_delete(self, attachment_id: str, user_id: str = None) -> Dict:
        """Handle DELETE /api/email-attachment/{id} request."""
        return self.email_handlers.handle_email_attachment_delete(attachment_id, user_id)

    def handle_email_delete(self, email_id: str, user_id: str = None) -> Dict:
        """Handle DELETE /api/email/{id} request."""
        return self.email_handlers.handle_email_delete(email_id, user_id)

    def handle_email_resync(self, email_id: str, provider_message_id: str, user_id: str) -> Dict:
        """Handle POST /api/email/{id}/resync request."""
        return self.email_handlers.repository.resync_email_from_gmail(email_id, provider_message_id, user_id)

    def handle_extract_contact_from_email(self, email_id: str = None, email_body: str = None, user_id: str = None) -> Dict:
        """Handle /api/email/extract-contact request."""
        return self.email_handlers.handle_extract_contact_from_email(email_id=email_id, email_body=email_body, user_id=user_id)

    def handle_get_email_auth_status(self, email_id: str, user_id: str) -> Dict:
        """Handle /api/email/auth/{email_id} request."""
        return self.email_handlers.handle_get_email_auth_status(email_id=email_id, user_id=user_id)

    def handle_get_high_risk_senders(self, user_id: str) -> Dict:
        """Handle /api/email/senders/high-risk request."""
        return self.email_handlers.handle_get_high_risk_senders(user_id=user_id)

    def handle_get_verified_senders(self, user_id: str) -> Dict:
        """Handle /api/email/senders/verified request."""
        return self.email_handlers.handle_get_verified_senders(user_id=user_id)

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/document/extract-rfp request."""
        return self.business_handlers.handle_extract_rfp_from_document(document_id=document_id, user_id=user_id)

    # Action management operations
    def handle_list_actions(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Handle /api/opportunities/{id}/actions request."""
        return self.action_handlers.handle_list_actions(opportunity_id, user_id)
    
    def handle_create_action(self, data: Dict, user_id: str) -> Dict:
        """Handle POST /api/actions request."""
        return self.action_handlers.handle_create_action(data, user_id)
    
    def handle_get_action(self, action_id: str, user_id: str = None) -> Dict:
        """Handle GET /api/actions/{id} request."""
        return self.action_handlers.handle_get_action(action_id, user_id)
    
    def handle_update_action(self, action_id: str, data: Dict, user_id: str) -> Dict:
        """Handle PUT /api/actions/{id} request."""
        return self.action_handlers.handle_update_action(action_id, data, user_id)
    
    def handle_delete_action(self, action_id: str, user_id: str) -> Dict:
        """Handle DELETE /api/actions/{id} request."""
        return self.action_handlers.handle_delete_action(action_id, user_id)
    
    def handle_pause_action(self, action_id: str, user_id: str) -> Dict:
        """Handle POST /api/actions/{id}/pause request."""
        return self.action_handlers.handle_pause_action(action_id, user_id)
    
    def handle_resume_action(self, action_id: str, user_id: str) -> Dict:
        """Handle POST /api/actions/{id}/resume request."""
        return self.action_handlers.handle_resume_action(action_id, user_id)
    
    def handle_execute_action(self, action_id: str, user_id: str) -> Dict:
        """Handle POST /api/actions/{id}/execute request."""
        return self.action_handlers.handle_execute_action(action_id, user_id)
    
    def handle_get_action_logs(self, action_id: str, limit: int = 50, user_id: str = None) -> Dict:
        """Handle GET /api/actions/{id}/logs request."""
        return self.action_handlers.handle_get_action_logs(action_id, limit, user_id)
