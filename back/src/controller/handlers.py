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
from src.api.product.handler import ProductController
from src.controller.business_handler import BusinessHandlers
from src.controller.email_handler import EmailHandlers
from src.controller.classify_handler import ClassifyHandler
from src.controller.action_handlers import ActionHandlers
from src.infrastructure.clients.database import DatabaseHandler
from src.api.auth.handler import AuthHandler
from src.api.quote.handler import Quote as QuoteController
from src.domain.enums import OpportunityStage
from src.infrastructure.factory import ServiceFactory


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
        self.service_factory = ServiceFactory()

        try:
            db_handler = DatabaseHandler()
            self.database_handlers = DatabaseHandlers(db_handler)
        except Exception as e:
            print(f"[Rag] Warning: Could not initialize DatabaseHandler: {e}")

    def _serialize_domain_entity(self, entity: Any) -> Dict[str, Any]:
        """Convert dataclass entities to JSON-serializable dictionaries."""
        payload = asdict(entity)
        for key, value in payload.items():
            if isinstance(value, Enum):
                payload[key] = value.value
        return payload

    # Auth operations
    def handle_auth_signup(self, body: bytes) -> Dict:
        """Handle /api/auth/signup request."""
        auth_handler = AuthHandler()
        return auth_handler.handle_signup(body)

    def handle_auth_login(self, body: bytes) -> Dict:
        """Handle /api/auth/login request."""
        auth_handler = AuthHandler()
        return auth_handler.handle_login(body)

    def handle_auth_logout(self, auth_header: str) -> Dict:
        """Handle /api/auth/logout request."""
        auth_handler = AuthHandler()
        return auth_handler.handle_logout(auth_header)

    def handle_auth_user(self, auth_header: str) -> Dict:
        """Handle /api/auth/user request."""
        auth_handler = AuthHandler()
        return auth_handler.handle_get_user(auth_header)
                    
    

    # CSV file operations
    def handle_list_products(self, qs: Dict) -> Dict:
        """Handle /api/products list request."""
        controller = ProductController()
        products = controller.list(qs)
        return {"products": products}

    def handle_create_product(self, payload: Dict) -> Dict:
        """Handle /api/products create request."""
        controller = ProductController()
        entity = controller.post(payload)
        return {"status": "ok", "product": entity}

    def handle_csv_source_upload(self, content_type: str, content_length: int, body: bytes) -> Dict:
        """Handle /api/csv/source upload request."""
        return self.file_handler.handle_file_upload(content_type, content_length, body)

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

    def handle_update_quote(self, document_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Handle /api/quote/{id} update request."""
        controller = QuoteController()
        return controller.update(document_id=document_id, payload=payload, user_id=user_id)

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        """Handle /api/rfq/generate request."""
        return self.business_handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Handle /api/opportunity/{id}/rfq/generate request."""
        return self.business_handlers.handle_generate_quote_for_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
        )

    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Handle /api/quote/{id}/pdf request."""
        return self.business_handlers.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Handle /api/opportunity/{id}/send-quote request."""
        return self.business_handlers.handle_send_quote_for_opportunity(
            opportunity_id=opportunity_id,
            payload=payload,
            user_id=user_id,
        )

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

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        """Handle /api/document/update-content request."""
        return self.business_handlers.handle_update_document_content(
            document_id=document_id,
            content=content,
            user_id=user_id,
        )

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
            self.business_handlers.handle_generate_quote_for_opportunity(
                opportunity_id=opportunity_id,
                user_id=user_id,
            )

        return result

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        """Handle /api/opportunities/create-manual request."""
        return self.business_handlers.handle_create_opportunity_manual(
            user_id=user_id,
            name=name,
        )
    
    def handle_search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None) -> Dict:
        """Handle /api/opportunities/search request."""
        return self.business_handlers.handle_search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )
    
    def handle_delete_opportunity(self, opportunity_ids: str, user_id: str = None) -> Dict:
        """Handle DELETE /api/opportunities/{ids} request. Supports single or comma-separated IDs."""
        # Parse IDs - can be single ID or comma-separated list
        ids_list = [id.strip() for id in opportunity_ids.split(',') if id.strip()]
        return self.business_handlers.handle_delete_opportunities(
            opportunity_ids=ids_list,
            user_id=user_id,
        )
    
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

    def handle_classify_unclassified(
        self,
        user_id: str,
        limit: int = 200,
    ) -> Dict:
        """Handle /api/gmail/classify-unclassified request."""
        return self.email_handlers.handle_classify_unclassified(
            user_id=user_id,
            limit=limit,
        )

    def handle_classify_email(self, email_uuid: str, user_id: str, force: bool = True) -> Dict:
        """Handle /api/emails/classify/{id} request."""
        classify_handler = ClassifyHandler()
        return classify_handler.handle_classify(email_uuid, user_id, force)
    
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
        return self.email_handlers.handle_email_resync(email_id, provider_message_id, user_id)

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
