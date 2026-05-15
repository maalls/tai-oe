"""Document-related request handlers."""

from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text, extract_rfp_from_text
from src.service.opportunity.document_content_service import DocumentContentService
from src.service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


class DocumentHandlers:
    """Handle document-related API requests."""

    def __init__(
        self,
        supabase=None,
        storage_dir_resolver: Callable = None,
        storage_path_resolver: Callable = None,
        clean_email_body: Callable = None,
        enrich_rfp: Callable = None,
    ):
        self.supabase = supabase or get_supabase_service()
        self.storage_dir_resolver = storage_dir_resolver
        self.storage_path_resolver = storage_path_resolver
        self.clean_email_body = clean_email_body
        self.enrich_rfp = enrich_rfp
        self._document_content_service = None
        self._document_rfp_extraction_service = None

    @property
    def document_content_service(self) -> DocumentContentService:
        if self._document_content_service is None:
            self._document_content_service = DocumentContentService(
                supabase=self.supabase,
                storage_dir_resolver=self.storage_dir_resolver,
            )
        return self._document_content_service

    @property
    def document_rfp_extraction_service(self) -> DocumentRfpExtractionService:
        if self._document_rfp_extraction_service is None:
            self._document_rfp_extraction_service = DocumentRfpExtractionService(
                supabase=self.supabase,
                storage_path_resolver=self.storage_path_resolver,
                clean_email_body=self.clean_email_body,
                extract_rfp=extract_rfp_from_text,
                extract_company=extract_company_from_text,
                enrich_rfp=self.enrich_rfp,
            )
        return self._document_rfp_extraction_service

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_content_service.update_document_content(
            document_id=document_id,
            content=content,
        )

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_rfp_extraction_service.extract_from_document(document_id=document_id)
