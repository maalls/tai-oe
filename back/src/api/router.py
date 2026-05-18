"""Main request handlers orchestration for the RAG server."""

from typing import Dict
from pathlib import Path

from src.api.file.handler import FileHandler
from src.api.csv.handler import CsvHandlers
from src.api.database.handler import DatabaseHandlers
from src.api.email.handler import EmailHandlers
from src.api.document.handler import DocumentHandlers
from src.api.entity.handler import EntityHandlers
from src.api.invoice.handler import InvoiceHandlers
from src.api.opportunity.handler import OpportunityHandlers
from src.api.rfq.handler import RfqHandlers
from src.api.quote.handler import Quote as QuoteController
from src.api.action.handler import ActionHandlers
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.clients.supabase import get_supabase_service
from src.infrastructure.factory import ServiceFactory
from src.lib.encoders.embeddings import EmbeddingGenerator
from src.lib.storage_paths import get_storage_dir, get_storage_path
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.service.email.opportunity_from_email_service import OpportunityFromEmailService


class RouterBusinessFacade:
    """Local composition facade replacing legacy BusinessHandlers file."""

    def __init__(self, service_factory: ServiceFactory = None, email_handlers: EmailHandlers = None):
        self.email_handlers = email_handlers or EmailHandlers()
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
        self.quote_handlers = QuoteController()
        self.entity_handlers = EntityHandlers(supabase=self.supabase)
        self.invoice_handlers = InvoiceHandlers(
            supabase=self.supabase,
            send_email_with_attachments=self.email_handlers.handle_send_email_with_attachments,
            storage_path_resolver=get_storage_path,
        )
        self.document_handlers = DocumentHandlers(
            supabase=self.supabase,
            storage_dir_resolver=get_storage_dir,
            storage_path_resolver=get_storage_path,
            clean_email_body=EmailRepository._clean_email_body,
            enrich_rfp=lambda message_clean, pre_extracted_data: self.opportunity_repository._extract_and_enrich_rfp_data(
                message_clean,
                pre_extracted_data=pre_extracted_data,
            ),
        )

    def handle_rfp_upload(self, body: bytes, content_type: str) -> Dict:
        return self.rfq_handlers.handle_rfp_upload(body=body, content_type=content_type)

    def handle_quote_submit(self, body: bytes, content_type: str) -> Dict:
        _ = content_type
        return self.quote_handlers.handle_quote_submit(body)

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None) -> Dict:
        return self.opportunity_handlers.handle_generate_quote_with_content(
            opportunity_id=opportunity_id,
            content=content,
            user_id=user_id,
        )

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        return self.opportunity_handlers.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        return self.opportunity_handlers.handle_create_opportunity_manual(user_id=user_id, name=name)

    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None) -> Dict:
        return self.opportunity_handlers.handle_search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None) -> Dict:
        return self.opportunity_handlers.handle_delete_opportunities(opportunity_ids=opportunity_ids, user_id=user_id)

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        return self.document_handlers.handle_update_document_content(document_id=document_id, content=content, user_id=user_id)

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        return self.email_handlers.handle_create_opportunity_from_email(message_id, user_id)

    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_opportunity_from_rfp(body=body, content_type=content_type, user_id=user_id)

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        return self.quote_handlers.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)

    def handle_update_entity_field(self, table: str, field: str, record_id: str, value, user_id: str = None) -> Dict:
        return self.entity_handlers.handle_update_entity_field(
            table=table,
            field=field,
            record_id=record_id,
            value=value,
            user_id=user_id,
        )

    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        return self.document_handlers.handle_delete_quote_document(document_id=document_id, user_id=user_id)

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        return self.document_handlers.handle_delete_document(document_id=document_id, user_id=user_id)

    def handle_list_quotes(self) -> Dict:
        return self.quote_handlers.handle_list_quotes()

    def handle_get_quote_file(self, filename: str) -> bytes:
        return self.quote_handlers.handle_get_quote_file(filename)

    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        return self.email_handlers.handle_quote_send(body, content_type)

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        return self.email_handlers.handle_send_quote_for_opportunity(
            opportunity_id=opportunity_id,
            payload=payload,
            user_id=user_id,
        )

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        return self.document_handlers.handle_extract_rfp_from_document(document_id=document_id, user_id=user_id)

    def handle_create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_rfq_source_from_html_body(
            opportunity_id=opportunity_id,
            body=body,
            content_type=content_type,
            user_id=user_id,
        )

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str) -> Dict:
        return self.document_handlers.handle_chat_attachment_upload(
            body=body,
            content_type=content_type,
            user_id=user_id,
            opportunity_id=opportunity_id,
        )

    def handle_update_line_verification(
        self,
        document_id: str,
        line_index: int,
        verification_fields: dict = None,
        is_ref_verified: bool = None,
        user_id: str = None,
    ) -> Dict:
        return self.document_handlers.handle_update_line_verification(
            document_id=document_id,
            line_index=line_index,
            verification_fields=verification_fields,
            is_ref_verified=is_ref_verified,
            user_id=user_id,
        )

    def handle_get_document_file(self, filename: str) -> bytes:
        return self.document_handlers.handle_get_document_file(filename)

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        return self.invoice_handlers.handle_generate_invoice_from_quote(quote_id=quote_id, user_id=user_id)

    def handle_send_invoice(self, invoice_id: str, payload: Dict, user_id: str = None) -> Dict:
        return self.invoice_handlers.handle_send_invoice(invoice_id=invoice_id, payload=payload, user_id=user_id)

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
        return self.invoice_handlers.handle_generate_invoice_pdf(document_id=document_id, user_id=user_id)


class RequestHandlers:
    """HTTP request handlers orchestration layer."""
    
    def __init__(
        self,
        file_handler: FileHandler,
    ):
        self.file_handler = file_handler
        self._embedding_generator = None
        # Delegate to specialized handlers
        self.csv_handlers = CsvHandlers(file_handler)
        self.email_handlers = EmailHandlers()
        self.action_handlers = ActionHandlers()
        self.service_factory = ServiceFactory()
        self.business_handlers = RouterBusinessFacade(
            service_factory=self.service_factory,
            email_handlers=self.email_handlers,
        )

        try:
            db_handler = DatabaseHandler()
            self.database_handlers = DatabaseHandlers(db_handler)
        except Exception as e:
            print(f"[Rag] Warning: Could not initialize DatabaseHandler: {e}")

    @property
    def embedding_generator(self) -> EmbeddingGenerator:
        if self._embedding_generator is None:
            print("[Rag] Initializing embedding generator...")
            self._embedding_generator = EmbeddingGenerator()
        return self._embedding_generator

    @property
    def opportunity_from_email_service(self) -> OpportunityFromEmailService:
        if getattr(self, "_opportunity_from_email_service", None) is None:
            self._opportunity_from_email_service = OpportunityFromEmailService(
                create_opportunity_from_email=self.business_handlers.handle_create_opportunity_from_email,
                generate_quote_for_opportunity=self.business_handlers.handle_generate_quote_for_opportunity,
            )
        return self._opportunity_from_email_service

    def handle_get_prompt_content(self, relative_path: str, prompt_base_dir: Path) -> str:
        """Resolve and read prompt markdown content safely."""
        if not relative_path:
            raise ValueError("Missing prompt path")

        prompt_path = (prompt_base_dir / relative_path / 'prompt.md').resolve()
        if prompt_base_dir not in prompt_path.parents:
            raise ValueError("Invalid prompt path")
        if not prompt_path.exists():
            raise FileNotFoundError("Prompt not found")

        return prompt_path.read_text(encoding='utf-8')


