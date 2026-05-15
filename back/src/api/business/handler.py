"""Business-related request handlers for RFP and other business operations."""

from typing import Dict
import os
import time
from datetime import datetime
from pathlib import Path
from io import BytesIO
from html.parser import HTMLParser

from src.api.email.handler import EmailHandlers
from src.api.document.handler import DocumentHandlers
from src.api.entity.handler import EntityHandlers
from src.api.invoice.handler import InvoiceHandlers
from src.api.opportunity.handler import OpportunityHandlers
from src.api.quote.handler import Quote
from src.api.rfq.handler import RfqHandlers
from src.infrastructure.factory import ServiceFactory
from src.infrastructure.clients.supabase import get_supabase_service
from src.repository.email_repository import EmailRepository
from src.lib.email.html_parser import Parser
from src.repository.opportunity import OpportunityRepository


class BusinessHandlers:
    """Handle business-related API requests."""
    
    def __init__(self, service_factory: ServiceFactory = None):
        """Initialize business handlers."""
        self.email_handlers = EmailHandlers()
        self.email_repository = EmailRepository()
        self.service_factory = service_factory or ServiceFactory()
        self.opportunity_repository = OpportunityRepository()
        self.supabase = get_supabase_service()
        self.rfq_handlers = RfqHandlers(
            service_factory=self.service_factory,
            email_repository=self.email_repository,
            opportunity_repository=self.opportunity_repository,
        )
        self.opportunity_handlers = OpportunityHandlers(
            service_factory=self.service_factory,
            email_repository=self.email_repository,
            opportunity_repository=self.opportunity_repository,
            supabase=self.supabase,
        )
        self.quote_handlers = Quote()
        self.entity_handlers = EntityHandlers(supabase=self.supabase)
        self.invoice_handlers = InvoiceHandlers(
            supabase=self.supabase,
            send_email_with_attachments=self.email_handlers.handle_send_email_with_attachments,
            storage_path_resolver=self._get_storage_path,
        )
        self.document_handlers = DocumentHandlers(
            supabase=self.supabase,
            storage_dir_resolver=self._get_storage_dir,
            storage_path_resolver=self._get_storage_path,
            clean_email_body=self._clean_email_body,
            enrich_rfp=lambda message_clean, pre_extracted_data: self.opportunity_repository._extract_and_enrich_rfp_data(
                message_clean,
                pre_extracted_data=pre_extracted_data,
            ),
        )

    @staticmethod
    def _clean_email_body(email_body: str, max_length: int = 3000) -> str:
        return EmailRepository._clean_email_body(email_body, max_length=max_length)

    def handle_rfp_upload(self, body: bytes, content_type: str) -> Dict:
        """Delegate RFP upload parsing/extraction to RFQ handler."""
        return self.rfq_handlers.handle_rfp_upload(body=body, content_type=content_type)

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        """Delegate RFQ draft generation to the dedicated RFQ handler."""
        return self.rfq_handlers.handle_rfq_generate(
            text=text,
            message_id=message_id,
            user_id=user_id,
        )

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None) -> Dict:
        return self.opportunity_handlers.handle_generate_quote_with_content(
            opportunity_id=opportunity_id,
            content=content,
            user_id=user_id,
        )

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Delegate quote generation for an opportunity to the current opportunity backend."""
        return self.opportunity_handlers.handle_generate_quote_for_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
        )

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        """Create an opportunity manually via the current opportunity backend."""
        return self.opportunity_handlers.handle_create_opportunity_manual(
            user_id=user_id,
            name=name,
        )

    def handle_search_opportunities(
        self,
        user_id: str,
        source_reference_id: str = None,
        name: str = None,
    ) -> Dict:
        """Search opportunities via the current opportunity backend."""
        return self.opportunity_handlers.handle_search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None) -> Dict:
        """Delete one or more opportunities via the current opportunity backend."""
        return self.opportunity_handlers.handle_delete_opportunities(
            opportunity_ids=opportunity_ids,
            user_id=user_id,
        )

    


    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        """Update the content of a document stored as a text file.
        
        Parameters
        ----------
        document_id : str
            Document ID
        content : str
            New content to save
        user_id : str
            User ID from auth
            
        Returns
        -------
        Dict
            Result with status
        """
        return self.document_handlers.handle_update_document_content(
            document_id=document_id,
            content=content,
            user_id=user_id,
        )

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        """Create a new_lead opportunity from an email message.
        
        Process:
        1. Classify email to determine category (RFQ, RFP, Quote, etc.)
        2. Extract contact and product info from email
        3. Create or find account based on email sender
        4. Create opportunity record with prefilled data
        """
        return self.email_handlers.handle_create_opportunity_from_email(message_id, user_id)
    
    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_opportunity_from_rfp(
            body=body,
            content_type=content_type,
            user_id=user_id,
        )
    
    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate quote PDF via dedicated quote handler."""
        return self.quote_handlers.handle_generate_quote_pdf(
            document_id=document_id,
            user_id=user_id,
        )

        

    def handle_update_entity_field(self, table: str, field: str, record_id: str, value, user_id: str = None) -> Dict:
        """Update a single field via EntityHandlers."""
        return self.entity_handlers.handle_update_entity_field(
            table=table,
            field=field,
            record_id=record_id,
            value=value,
            user_id=user_id,
        )
    
    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete a quote document and its related data via DocumentHandlers."""
        return self.document_handlers.handle_delete_quote_document(
            document_id=document_id,
            user_id=user_id,
        )

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete any document and its related data via DocumentHandlers."""
        return self.document_handlers.handle_delete_document(
            document_id=document_id,
            user_id=user_id,
        )
    
    def handle_list_quotes(self) -> Dict:
        """List all generated quotes via the dedicated quote handler."""
        return self.quote_handlers.handle_list_quotes()
    
    def handle_get_quote_file(self, filename: str) -> bytes:
        """Retrieve a quote PDF file via the dedicated quote handler."""
        return self.quote_handlers.handle_get_quote_file(filename)
    
    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        """Delegate quote send flow to EmailHandlers."""
        return self.email_handlers.handle_quote_send(body, content_type)

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Delegate quote send for an opportunity to EmailHandlers."""
        return self.email_handlers.handle_send_quote_for_opportunity(
            opportunity_id=opportunity_id,
            payload=payload,
            user_id=user_id,
        )

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        """Get storage directory path based on source type.
        
        Parameters
        ----------
        source : str
            Source type (e.g., 'rfp_upload', 'email', 'quote', etc.)
        
        Returns
        -------
        Path
            Storage directory for the source type
        """
        base_storage = Path("var/storage")
        
        # Map source types to storage subdirectories
        source_map = {
            "rfp_upload": "rfp_uploads",
            "email": "emails",
            "quote": "quotes",
            "invoice": "invoices",
            "attachment": "attachments"
        }
        
        subdir = source_map.get(source, source)
        storage_dir = base_storage / subdir
        
        return storage_dir
    
    @staticmethod
    def _get_storage_path(source: str, filename: str) -> Path:
        """Get full file path in storage based on source type and filename.
        
        Parameters
        ----------
        source : str
            Source type (e.g., 'rfp_upload', 'email', etc.)
        filename : str
            Filename within the storage directory
        
        Returns
        -------
        Path
            Full file path
        """
        storage_dir = BusinessHandlers._get_storage_dir(source)
        return storage_dir / filename

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        """Extract RFP data from a document (PDF or text file).
        
        Process:
        1. Get document from database
        2. Read file from storage
        3. Extract text (PDF or plain text)
        4. Extract RFP data using LLM
        5. Return extracted products and contact info
        
        Parameters
        ----------
        document_id : str
            Document ID to extract from
        user_id : str
            User ID from auth
        
        Returns
        -------
        Dict
            Result with extracted RFP data
        """
        return self.document_handlers.handle_extract_rfp_from_document(
            document_id=document_id,
            user_id=user_id,
        )

    def handle_create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_rfq_source_from_html_body(
            opportunity_id=opportunity_id,
            body=body,
            content_type=content_type,
            user_id=user_id,
        )

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str) -> Dict:
        """Handle chat attachment upload via DocumentHandlers."""
        return self.document_handlers.handle_chat_attachment_upload(
            body=body,
            content_type=content_type,
            user_id=user_id,
            opportunity_id=opportunity_id,
        )
        

    def handle_update_line_verification(self, document_id: str, line_index: int, verification_fields: dict = None, is_ref_verified: bool = None, user_id: str = None) -> Dict:
        """Update line verification via DocumentHandlers."""
        return self.document_handlers.handle_update_line_verification(
            document_id=document_id,
            line_index=line_index,
            verification_fields=verification_fields,
            is_ref_verified=is_ref_verified,
            user_id=user_id,
        )

    def handle_get_document_file(self, filename: str) -> bytes:
        """Retrieve a document file via DocumentHandlers."""
        return self.document_handlers.handle_get_document_file(filename)

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        """Generate an invoice document via InvoiceHandlers."""
        return self.invoice_handlers.handle_generate_invoice_from_quote(
            quote_id=quote_id,
            user_id=user_id,
        )

    def handle_send_invoice(self, invoice_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Send invoice via InvoiceHandlers."""
        return self.invoice_handlers.handle_send_invoice(
            invoice_id=invoice_id,
            payload=payload,
            user_id=user_id,
        )

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate an invoice PDF via InvoiceHandlers."""
        return self.invoice_handlers.handle_generate_invoice_pdf(
            document_id=document_id,
            user_id=user_id,
        )