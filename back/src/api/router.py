"""Main request handlers orchestration for the RAG server."""

from dataclasses import asdict
from enum import Enum
from typing import Optional, Dict, Any, Iterator
import urllib.request
import urllib.parse
from pathlib import Path
import json
import os

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
from src.domain.enums import OpportunityStage
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

    def _serialize_domain_entity(self, entity: Any) -> Dict[str, Any]:
        """Convert dataclass entities to JSON-serializable dictionaries."""
        payload = asdict(entity)
        for key, value in payload.items():
            if isinstance(value, Enum):
                payload[key] = value.value
        return payload

    @property
    def opportunity_from_email_service(self) -> OpportunityFromEmailService:
        if getattr(self, "_opportunity_from_email_service", None) is None:
            self._opportunity_from_email_service = OpportunityFromEmailService(
                create_opportunity_from_email=self.business_handlers.handle_create_opportunity_from_email,
                generate_quote_for_opportunity=self.business_handlers.handle_generate_quote_for_opportunity,
            )
        return self._opportunity_from_email_service

    # Utility operations used by server/file routes
    def handle_fetch_url(self, target_url: str, max_chars: int, timeout_ms: int) -> Dict:
        """Handle /api/fetch request."""
        with urllib.request.urlopen(target_url, timeout=timeout_ms / 1000) as resp:
            content_type = resp.headers.get('Content-Type', '')
            status = getattr(resp, 'status', 200)
            raw = resp.read()

        text = raw.decode('utf-8', errors='replace')
        truncated = text[:max_chars]

        return {
            'status': status,
            'ok': status >= 200 and status < 300,
            'url': target_url,
            'content_type': content_type,
            'truncated': len(text) > max_chars,
            'text': truncated,
        }

    def handle_curl_request(
        self,
        target_url: str,
        method: str,
        headers: Dict[str, str],
        body_text: str,
        max_chars: int,
        timeout_ms: int,
    ) -> Dict:
        """Handle /api/curl request."""
        data_bytes = body_text.encode('utf-8') if body_text is not None else None
        req = urllib.request.Request(target_url, data=data_bytes, method=method)
        for key, value in headers.items():
            if isinstance(key, str) and isinstance(value, str):
                req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
            content_type = resp.headers.get('Content-Type', '')
            status = getattr(resp, 'status', 200)
            raw = resp.read()

        text = raw.decode('utf-8', errors='replace')
        truncated = text[:max_chars]

        return {
            'status': status,
            'ok': status >= 200 and status < 300,
            'url': target_url,
            'content_type': content_type,
            'truncated': len(text) > max_chars,
            'text': truncated,
        }

    def handle_fs_create(self, target_path: Path, kind: str) -> Dict:
        """Handle /api/fs/create request after path validation."""
        if kind == 'file':
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch(exist_ok=True)
            if not target_path.exists() or not target_path.is_file():
                raise RuntimeError('file not created')
        else:
            target_path.mkdir(parents=True, exist_ok=True)
            if not target_path.exists() or not target_path.is_dir():
                raise RuntimeError('directory not created')

        return {
            'status': 'ok',
            'path': str(target_path),
            'type': 'file' if kind == 'file' else 'dir',
        }

    def handle_fs_read(self, target_path: Path, max_chars: int) -> Dict:
        """Handle /api/fs/read request after path and existence validation."""
        content = target_path.read_text(encoding='utf-8', errors='replace')
        truncated = content[:max_chars]
        return {
            'status': 'ok',
            'path': str(target_path),
            'truncated': len(content) > max_chars,
            'text': truncated,
        }

    def handle_email_fetch_loop_status(self, status_path: Path, legacy_path: Path) -> Dict:
        """Handle /api/email-fetch-loop/status request."""
        if not status_path.exists() and legacy_path.exists():
            status_path = legacy_path

        if not status_path.exists():
            return {
                'running': False,
                'pid': None,
                'started_at': None,
                'last_heartbeat': None,
                'mode': None,
            }

        try:
            payload = json.loads(status_path.read_text(encoding='utf-8') or '{}')
        except Exception:
            payload = {}

        pid = payload.get('pid')
        running = False
        if pid:
            try:
                os.kill(int(pid), 0)
                running = True
            except Exception:
                running = False

        return {
            'running': running,
            'pid': pid,
            'started_at': payload.get('started_at'),
            'last_heartbeat': payload.get('last_heartbeat'),
            'mode': payload.get('mode'),
        }

    def handle_storage_find_path(self, storage_dir: Path, filename: str) -> Optional[Path]:
        """Locate a storage file across known subdirectories then root storage."""
        storage_subdirs = ['rfp_uploads', 'attachment', 'attachments', 'email', 'quotes']
        for subdir in storage_subdirs:
            candidate = storage_dir / subdir / filename
            if candidate.exists():
                return candidate

        root_candidate = storage_dir / filename
        if root_candidate.exists():
            return root_candidate

        return None

    def handle_storage_sanitize_filename(self, raw_filename: str) -> str:
        """Sanitize filename from storage routes to prevent traversal."""
        filename = urllib.parse.unquote(raw_filename)
        return filename.replace('..', '').replace('/', '')

    def handle_storage_file_metadata(self, filename: str, storage_path: Path) -> Dict[str, Any]:
        """Build storage file metadata and headers needed by HEAD/GET responses."""
        file_ext = storage_path.suffix.lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain; charset=utf-8',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
        }
        content_type = content_type_map.get(file_ext, 'application/octet-stream')
        file_size = storage_path.stat().st_size
        encoded_filename = urllib.parse.quote(filename)
        disposition = 'inline' if content_type == 'application/pdf' else 'attachment'

        return {
            'content_type': content_type,
            'file_size': file_size,
            'content_disposition': f"{disposition}; filename*=UTF-8''{encoded_filename}",
        }

    def handle_storage_resolve_file(self, storage_dir: Path, raw_filename: str) -> Dict[str, Any]:
        """Resolve a storage file and compute metadata from a raw route filename."""
        filename = self.handle_storage_sanitize_filename(raw_filename)
        storage_path = self.handle_storage_find_path(storage_dir, filename)
        if not storage_path or not storage_path.exists():
            raise FileNotFoundError(f"Storage file not found: {filename}")

        metadata = self.handle_storage_file_metadata(filename, storage_path)
        return {
            'filename': filename,
            'storage_path': storage_path,
            'metadata': metadata,
        }

    def handle_storage_read_chunks(self, storage_path: Path, chunk_size: int = 8192) -> Iterator[bytes]:
        """Yield file content as chunks for storage streaming responses."""
        with open(storage_path, 'rb') as file_handle:
            while True:
                chunk = file_handle.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def handle_storage_response_headers(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Build HTTP headers for storage HEAD/GET responses from metadata."""
        return {
            'Content-Type': metadata['content_type'],
            'Content-Length': str(metadata['file_size']),
            'Accept-Ranges': 'bytes',
            'Content-Disposition': metadata['content_disposition'],
        }

    def handle_storage_not_found_payload(self, raw_filename: str, include_body: bool = False) -> Dict[str, Any]:
        """Build normalized 404 payload pieces for storage routes."""
        filename = self.handle_storage_sanitize_filename(raw_filename)
        payload: Dict[str, Any] = {
            'filename': filename,
            'content_type': 'text/plain',
        }
        if include_body:
            payload['body'] = b'File not found'
        return payload

    def handle_storage_read_error_payload(self, error: Exception) -> Dict[str, Any]:
        """Build normalized 500 payload for storage read failures."""
        message = f"Error reading file: {str(error)}"
        return {
            'content_type': 'text/plain',
            'body': message.encode('utf-8'),
            'message': message,
        }

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

    # New DDD services (incremental migration path)
    def handle_get_opportunity(self, opportunity_id: str) -> Dict:
        """Handle DDD get-opportunity use-case."""
        try:
            service = self.service_factory.create_opportunity_service()
            opportunity = service.get_opportunity(opportunity_id)
            return {
                "status": "ok",
                "opportunity": self._serialize_domain_entity(opportunity),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def handle_advance_opportunity(self, opportunity_id: str, stage: str) -> Dict:
        """Handle DDD advance-opportunity use-case."""
        try:
            parsed_stage = OpportunityStage(stage)
            service = self.service_factory.create_opportunity_service()
            opportunity = service.advance_opportunity(opportunity_id, parsed_stage)
            return {
                "status": "ok",
                "opportunity": self._serialize_domain_entity(opportunity),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def handle_get_vendor(self, vendor_id: str) -> Dict:
        """Handle DDD get-vendor use-case."""
        try:
            service = self.service_factory.create_vendor_service()
            vendor = service.get_vendor(vendor_id)
            return {
                "status": "ok",
                "vendor": self._serialize_domain_entity(vendor),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def handle_get_rfp(self, rfp_id: str) -> Dict:
        """Handle DDD get-rfp use-case."""
        try:
            service = self.service_factory.create_rfp_service()
            rfp = service.get_rfp(rfp_id)
            return {
                "status": "ok",
                "rfp": self._serialize_domain_entity(rfp),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def handle_submit_rfp(self, rfp_id: str) -> Dict:
        """Handle DDD submit-rfp use-case."""
        try:
            service = self.service_factory.create_rfp_service()
            rfp = service.submit_rfp(rfp_id)
            return {
                "status": "ok",
                "rfp": self._serialize_domain_entity(rfp),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

