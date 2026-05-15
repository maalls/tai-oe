#!/usr/bin/env python3
"""
Quote Management.s
Config via env:
- PORT (default 8088)
- STORAGE_DIR (default ./var/storage)
"""
import os
import sys
import re
import urllib.parse
import urllib.request
import http.server
import signal
import traceback
from pathlib import Path

from typing import Dict
from src.reader.csv import CSVReader
from src.embeddings import EmbeddingGenerator
from src.api.file.handler import FileHandler
from src.api.router import RequestHandlers
from src.api.auth.handler import AuthHandler
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.infrastructure.runtime.http_server import ReusableThreadingHTTPServer
from src.infrastructure.runtime.llm_health import test_llm_connection
from src.api.routes.ddd_get_routes import handle_ddd_get_route, is_ddd_get_route
from src.api.routes.ddd_post_routes import handle_ddd_post_route, is_ddd_post_route
from src.api.routes.server_delete_dispatch import dispatch_delete_request
from src.api.routes.server_auth_helpers import (
    authorize_request,
    get_optional_user_id_from_auth,
    require_auth,
    require_auth_user_id,
)
from src.api.routes.server_body_helpers import read_body, read_json, read_json_or_error
from src.api.routes.server_get_dispatch import dispatch_get_request
from src.api.routes.server_get_auth_handlers import (
    handle_auth_user_get,
    handle_oauth_callback_get,
    handle_oauth_login_get,
)
from src.api.routes.server_get_mail_basic_handlers import (
    handle_gmail_authorize_get,
    handle_gmail_oauth_start_get,
    handle_gmail_profile_get,
    handle_gmail_revoke_get,
    handle_gmail_status_get,
    handle_imap_config_get,
    handle_imap_status_get,
)
from src.api.routes.server_get_mail_message_handlers import (
    handle_email_attachment_get,
    handle_gmail_classify_unclassified_get,
    handle_gmail_message_get,
    handle_gmail_messages_get,
)
from src.api.routes.server_get_csv_handlers import (
    handle_csv_files_get,
    handle_csv_get,
    handle_csv_preview_get,
    handle_csv_query_get,
    handle_csv_search_get,
    handle_csv_sources_get,
)
from src.api.routes.server_get_download_handlers import handle_document_download, handle_quote_download
from src.api.routes.server_get_stream_handlers import handle_csv_download, handle_raw_stream, handle_source_stream
from src.api.routes.server_get_business_handlers import (
    handle_action_get,
    handle_action_logs_get,
    handle_documents_download_get,
    handle_opportunities_search_get,
    handle_opportunity_actions_list_get,
    handle_quotes_download_get,
    handle_quotes_list_get,
)
from src.api.routes.server_get_misc_handlers import (
    handle_fetch_get,
    handle_email_fetch_loop_status_get,
    handle_google_oauth_callback_get,
    handle_prompt_get,
    handle_products_get,
)
from src.api.routes.server_head_dispatch import dispatch_head_request
from src.api.routes.server_mutation_dispatch import dispatch_patch_request, dispatch_put_request
from src.api.routes.server_path_helpers import resolve_fs_path
from src.api.routes.server_post_dispatch import dispatch_post_request
from src.api.routes.server_post_core_dispatch import dispatch_post_core_routes
from src.api.routes.server_post_legacy_dispatch import dispatch_action_post_routes, dispatch_post_legacy_and_action_routes
from src.api.routes.server_query_helpers import get_payload_int, get_qs_bool, get_qs_int, get_qs_value
from src.api.routes.server_response_helpers import send_error, send_json, send_redirect, send_text_response
from src.api.routes.server_post_auth_dispatch import dispatch_post_auth_routes
from src.api.routes.server_post_business_dispatch import dispatch_post_business_routes
from src.api.routes.server_post_domain_dispatch import dispatch_post_domain_routes
from src.api.routes.server_status_helpers import pop_status, status_from_error, status_from_result
from src.api.routes.server_storage_handlers import handle_storage_get, handle_storage_head

# Load .env before reading config values.
load_runtime_env(__file__)


config = {
    "PORT": int(os.environ.get("PORT", "8088")),
    "STORAGE_DIR": Path(os.environ.get("STORAGE_DIR", "var/storage")).resolve(),
    "SUPABASE_URL": os.environ.get("SUPABASE_URL"),
    "DATABASE_URL": os.environ.get("DATABASE_URL"),
}


def create_rag_handler(config):
    """Factory to create HTTP request handler with config."""
    
    class Rag(http.server.SimpleHTTPRequestHandler):
        # Shared resources (class variables)
        _embedding_generator = None
        _csv_reader = None
        _file_handler = None
        _request_handlers = None
        _auth_handler = None

        @classmethod
        def get_embedding_generator(cls):
            if cls._embedding_generator is None:
                print("[Rag] Initializing embedding generator...")
                cls._embedding_generator = EmbeddingGenerator()
            return cls._embedding_generator
        
        @classmethod
        def get_csv_reader(cls):
            if cls._csv_reader is None:
                cls._csv_reader = CSVReader()
            return cls._csv_reader
        
        @classmethod
        def get_file_handler(cls):
            if cls._file_handler is None:
                cls._file_handler = FileHandler(config["STORAGE_DIR"], cls.get_csv_reader())
            return cls._file_handler
        
        @classmethod
        def get_auth_handler(cls):
            if cls._auth_handler is None:
                cls._auth_handler = AuthHandler()
                print("[Rag] Initialized AuthHandler")
            return cls._auth_handler
        
        @classmethod
        def get_request_handlers(cls):
            if cls._request_handlers is None:
                cls._request_handlers = RequestHandlers(
                    cls.get_file_handler()
                )
            return cls._request_handlers
        
        def __init__(self, *args, **kwargs):
            self.config = config
            super().__init__(*args, **kwargs)

        def end_headers(self):
            # Only add wildcard CORS if we haven't already set a specific origin
            # Check if Access-Control-Allow-Origin header was already sent
            if not hasattr(self, '_cors_header_sent'):
                self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST, DELETE, PATCH')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.end_headers()

        def do_DELETE(self):
            try:
                print(f"[RAG] do_DELETE called with path: {self.path}", file=sys.stderr)
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_delete_request(self, parsed.path):
                    return
                
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return self._send_error(500, f"Server error: {str(e)}")

        def do_PATCH(self):
            try:
                parsed = urllib.parse.urlparse(self.path)
                print(f"[RAG] PATCH request to: {parsed.path}")
                if dispatch_patch_request(self, parsed.path):
                    return

                print(f"[RAG] PATCH path not matched: {parsed.path}")
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] PATCH error: {e}")
                return self._send_error(500, f"Server error: {str(e)}")

        def do_PUT(self):
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_put_request(self, parsed.path):
                    return
                
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return self._send_error(500, f"Server error: {str(e)}")

        def _handle_action_update_put(self, update_action_match):
            """Handle PUT /api/actions/{id}."""
            data = self._read_json_or_error()
            if data is None:
                return

            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            action_id = update_action_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_update_action(action_id, data, user_id)
            status = self._status_from_result(result)
            self.json(result, status)

        def _status_from_result(self, result: Dict, ok: int = 200, error: int = 400) -> int:
            """Map handler result payload status to HTTP status code."""
            return status_from_result(result, ok=ok, error=error)

        def _pop_status(self, result: Dict, default: int = 200) -> int:
            """Extract and remove status code from handler payload."""
            return pop_status(result, default=default)

        def _status_from_error(self, result: Dict, ok: int = 200, error: int = 400, key: str = 'error') -> int:
            """Map payload error field presence to HTTP status code."""
            return status_from_error(result, ok=ok, error=error, key=key)

        def _handle_imap_config_delete(self):
            """Handle DELETE /api/imap/config."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            handlers = self.get_request_handlers()
            result = handlers.handle_imap_config_delete(user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_action_delete(self, action_delete_match):
            """Handle DELETE /api/actions/{id}."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            action_id = action_delete_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_delete_action(action_id=action_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_delete(self, email_delete_match):
            """Handle DELETE /api/email/{id}."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            email_id = email_delete_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_email_delete(email_id=email_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_attachment_delete(self, attachment_delete_match):
            """Handle DELETE /api/email-attachment/{id}."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            attachment_id = attachment_delete_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_email_attachment_delete(attachment_id=attachment_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_document_delete(self, document_delete_match):
            """Handle DELETE /api/document/{id}."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            document_id = document_delete_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_delete_document(document_id=document_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_quote_delete(self, quote_delete_match):
            """Handle DELETE /api/quote/{id}."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            document_id = quote_delete_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_delete_quote_document(document_id=document_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunity_delete(self, opportunity_delete_match):
            """Handle DELETE /api/opportunities/{ids}."""
            print(f"[RAG] DELETE /api/opportunities matched, processing deletion", file=sys.stderr)
            user_data = self._require_auth()
            if user_data is None:
                print(f"[RAG] DELETE - Auth failed", file=sys.stderr)
                return

            user_id = user_data.get('id') if user_data else None
            opportunity_ids = opportunity_delete_match.group(1)
            print(f"[RAG] DELETE opportunity(ies) {opportunity_ids} for user {user_id}", file=sys.stderr)

            handlers = self.get_request_handlers()
            result = handlers.handle_delete_opportunity(opportunity_ids=opportunity_ids, user_id=user_id)
            status = self._status_from_result(result)
            print(f"[RAG] DELETE result: {result}", file=sys.stderr)
            return self.json(result, status)

        def do_POST(self):
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_post_request(self, parsed):
                    return

                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling request: {e}")
                
                return self._send_error(500, f"Internal server error 1: {e}")

        def do_HEAD(self):
            try:
                parsed = urllib.parse.urlparse(self.path)

                if dispatch_head_request(self, parsed.path):
                    return

                return self._send_error(404, "Not found")
            except Exception as e:
                return self._send_error(500, f"Internal server error 2: {e}")

        def _handle_storage_head(self, parsed_path: str):
            """Handle HEAD requests for storage files."""
            return handle_storage_head(self, config['STORAGE_DIR'], parsed_path)

        def _handle_ddd_post_routes(self, parsed):
            """Handle incremental DDD POST routes through API adapters."""
            if not is_ddd_post_route(parsed.path):
                return False

            # Mutating DDD routes require authentication.
            if self._require_auth() is None:
                return True

            payload = self._read_json(default={})
            if not isinstance(payload, dict):
                payload = {}

            handlers = self.get_request_handlers()
            handled, response_payload, status = handle_ddd_post_route(parsed.path, payload, handlers)
            if not handled:
                return False

            self.json(response_payload, status)
            return True

        def _handle_ddd_get_routes(self, parsed, qs):
            """Handle incremental DDD GET routes through API adapters."""
            if not is_ddd_get_route(parsed.path):
                return False

            if self._require_auth() is None:
                return True

            query = {key: values[0] for key, values in qs.items() if values}
            handlers = self.get_request_handlers()
            handled, payload, status = handle_ddd_get_route(parsed.path, query, handlers)
            if not handled:
                return False
            self.json(payload, status)
            return True

        def do_GET(self):
            try:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)

                if dispatch_get_request(self, parsed, qs):
                    return

                # Fallback to static file serving
                return super().do_GET()
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling GET request: {e}")

                return self._send_error(500, f"Internal server error 3: {e}")

        def _handle_storage_get(self, parsed_path: str):
            """Handle GET requests for storage files."""
            return handle_storage_get(self, config['STORAGE_DIR'], parsed_path)

        def _handle_post_opportunity_quote_invoice_routes(self, parsed):
            """Handle secondary POST routes for opportunity/quote/invoice flows."""
            return dispatch_post_business_routes(self, parsed)

        def _handle_post_core_routes(self, parsed_path: str) -> bool:
            """Handle core POST routes that map directly to controller helpers."""
            return dispatch_post_core_routes(self, parsed_path)

        def _handle_post_auth_routes(self, parsed_path: str) -> bool:
            """Handle auth POST routes."""
            return dispatch_post_auth_routes(self, parsed_path)

        def _handle_post_domain_routes(self, parsed) -> bool:
            """Handle entity/email/opportunity/imap/document POST routes."""
            return dispatch_post_domain_routes(self, parsed)

        def _handle_action_post_routes(self, parsed_path: str) -> bool:
            """Handle action-specific POST regex routes."""
            return dispatch_action_post_routes(self, parsed_path)

        def _handle_post_legacy_and_action_routes(self, parsed_path: str) -> bool:
            """Handle remaining legacy and action POST routes."""
            return dispatch_post_legacy_and_action_routes(self, parsed_path)

        def _handle_products_post(self):
            """Handle /api/products POST endpoint."""
            payload = self._read_json(default={})
            handlers = self.get_request_handlers()
            result = handlers.handle_create_product(payload)
            return self.json(result, 201)

        def _handle_fs_create_post(self):
            """Handle /api/fs/create POST endpoint."""
            payload = self._read_json(default={})
            raw_path = str(payload.get('path') or '').strip()
            kind = payload.get('type') or 'dir'

            target_path = self._resolve_fs_path(raw_path)
            if target_path is None:
                return

            try:
                handlers = self.get_request_handlers()
                result = handlers.handle_fs_create(target_path=target_path, kind=kind)
            except Exception as e:
                return self._send_error(500, f'Create failed: {e}')
            return self.json(result)

        def _handle_fs_read_post(self):
            """Handle /api/fs/read POST endpoint."""
            payload = self._read_json(default={})
            raw_path = str(payload.get('path') or '').strip()

            max_chars = self._get_payload_int(payload, 'max_chars', 10000)
            max_chars = max(100, min(max_chars, 50000))

            target_path = self._resolve_fs_path(raw_path)
            if target_path is None:
                return

            if not target_path.exists() or not target_path.is_file():
                return self._send_error(404, 'File not found')

            try:
                handlers = self.get_request_handlers()
                result = handlers.handle_fs_read(target_path=target_path, max_chars=max_chars)
            except Exception as e:
                return self._send_error(500, f'Read failed: {e}')
            return self.json(result)

        def _handle_curl_post(self):
            """Handle /api/curl POST endpoint."""
            payload = self._read_json(default={})

            target_url = str(payload.get('url') or '').strip()
            if not target_url:
                return self._send_error(400, 'Missing url')
            if not target_url.startswith('http://') and not target_url.startswith('https://'):
                return self._send_error(400, 'Invalid url scheme')

            method = str(payload.get('method') or 'GET').upper()
            if method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
                return self._send_error(400, 'Invalid method')

            headers = payload.get('headers') if isinstance(payload.get('headers'), dict) else {}
            body_text = payload.get('body') if isinstance(payload.get('body'), str) else None

            max_chars = self._get_payload_int(payload, 'max_chars', 10000)
            timeout_ms = self._get_payload_int(payload, 'timeout_ms', 8000)

            max_chars = max(100, min(max_chars, 50000))
            timeout_ms = max(1000, min(timeout_ms, 20000))

            try:
                handlers = self.get_request_handlers()
                result = handlers.handle_curl_request(
                    target_url=target_url,
                    method=method,
                    headers=headers,
                    body_text=body_text,
                    max_chars=max_chars,
                    timeout_ms=timeout_ms,
                )
                return self.json(result)
            except Exception as e:
                return self._send_error(500, f'Curl failed: {e}')

        def _handle_auth_signup_post(self):
            """Handle /api/auth/signup POST endpoint."""
            body = self._read_body()
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_signup(body)
            status = self._pop_status(result)
            return self.json(result, status)

        def _handle_auth_login_post(self):
            """Handle /api/auth/login POST endpoint."""
            body = self._read_body()
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_login(body)
            status = self._pop_status(result)
            return self.json(result, status)

        def _handle_auth_logout_post(self):
            """Handle /api/auth/logout POST endpoint."""
            auth_header = self.headers.get('Authorization', '')
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_logout(auth_header)
            status = self._pop_status(result)
            return self.json(result, status)

        def _handle_entity_update_post(self, entity_update_match):
            """Handle /api/entity/{table}/{field} POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            table = entity_update_match.group(1)
            field = entity_update_match.group(2)

            payload = self._read_json(default={})

            record_id = payload.get('id') or payload.get('record_id')
            if record_id is None:
                return self.json({"status": "error", "message": "Missing id"}, 400)

            if 'value' not in payload:
                return self.json({"status": "error", "message": "Missing value"}, 400)

            handlers = self.get_request_handlers()
            result = handlers.handle_update_entity_field(
                table=table,
                field=field,
                record_id=record_id,
                value=payload.get('value'),
                user_id=user_id,
            )
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_emails_classify_post(self, parsed_path):
            """Handle /api/emails/classify/{email_uuid} POST endpoint."""
            email_uuid = parsed_path.split('/')[-1]

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id')
            print(f"[RAG] Classify request for email {email_uuid} by user {user_id}")

            handlers = self.get_request_handlers()
            result = handlers.handle_classify_email(email_uuid=email_uuid, user_id=user_id, force=True)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_rfq_generate_post(self):
            """Handle /api/rfq/generate POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            payload = self._read_json(default={})

            text = payload.get('text') or payload.get('content')
            message_id = payload.get('message_id')

            handlers = self.get_request_handlers()
            result = handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunities_create_from_email_post(self):
            """Handle /api/opportunities/create-from-email POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            payload = self._read_json(default={})

            message_id = payload.get('message_id')
            if not message_id:
                return self.json({"error": "Missing message_id parameter"}, 400)

            handlers = self.get_request_handlers()
            result = handlers.handle_create_opportunity_from_email(message_id=message_id, user_id=user_id)
            print(f"[RAG] Create opportunity result: {result.get('status')}, {result}")
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunities_create_manual_post(self):
            """Handle /api/opportunities/create-manual POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            payload = self._read_json(default={})

            name = payload.get('name')
            if not name:
                return self.json({"status": "error", "message": "Missing name parameter"}, 400)

            handlers = self.get_request_handlers()
            result = handlers.handle_create_opportunity_manual(user_id=user_id, name=name)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunities_create_from_rfp_post(self):
            """Handle /api/opportunities/create-from-rfp POST endpoint."""
            body = self._read_body()
            content_type = self.headers.get('Content-Type', '')

            auth_header = self.headers.get('Authorization', '')
            print(f"[RAG] Auth header present: {bool(auth_header)}, header: {auth_header[:50] if auth_header else 'None'}")
            user_data = self._require_auth(auth_header=auth_header)
            print(f"[RAG] Token valid: {bool(user_data)}, user_data: {user_data}")
            if user_data is None:
                print(f"[RAG] Authorization failed for token: {auth_header[:50] if auth_header else 'None'}")
                return

            user_id = user_data.get('id') if user_data else None
            handlers = self.get_request_handlers()
            result = handlers.handle_create_opportunity_from_rfp(body=body, content_type=content_type, user_id=user_id)
            print(f"[RAG] Create opportunity from RFP result: {result.get('status')}")
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_extract_contact_post(self):
            """Handle /api/email/extract-contact POST endpoint."""
            payload = self._read_json(default={})

            email_id = payload.get('email_id')
            email_body = payload.get('email_body')

            if not email_body:
                return self.json({"error": "Missing email_body parameter"}, 400)

            auth_header = self.headers.get('Authorization', '')
            user_data = self._require_auth(auth_header=auth_header, required=False)
            user_id = user_data.get('id') if user_data else None
            print(f"[RAG] Extract contact - Auth valid: {bool(user_data)}, user_id: {user_id}, auth_header: {auth_header[:50]}")

            handlers = self.get_request_handlers()
            result = handlers.handle_extract_contact_from_email(email_id=email_id, email_body=email_body, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_auth_status_post(self, parsed_path):
            """Handle /api/email/auth/{email_id} POST endpoint."""
            email_id = parsed_path.split('/api/email/auth/')[-1]

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            if not user_id:
                return self.json({"error": "Unauthorized"}, 401)

            handlers = self.get_request_handlers()
            result = handlers.handle_get_email_auth_status(email_id=email_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_resync_post(self, parsed_path):
            """Handle /api/email/{email_id}/resync POST endpoint."""
            path_parts = parsed_path.split('/')
            email_id = path_parts[-2] if len(path_parts) >= 4 else None

            if not email_id:
                return self.json({"error": "Missing email_id"}, 400)

            payload = self._read_json(default={})
            provider_message_id = payload.get('provider_message_id')
            if not provider_message_id:
                return self.json({"error": "Missing provider_message_id"}, 400)

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            if not user_id:
                return self.json({"error": "Unauthorized"}, 401)

            handlers = self.get_request_handlers()
            result = handlers.handle_email_resync(email_id=email_id, provider_message_id=provider_message_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_senders_high_risk_post(self):
            """Handle /api/email/senders/high-risk POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            if not user_id:
                return self.json({"error": "Unauthorized"}, 401)

            handlers = self.get_request_handlers()
            result = handlers.handle_get_high_risk_senders(user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_email_senders_verified_post(self):
            """Handle /api/email/senders/verified POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            if not user_id:
                return self.json({"error": "Unauthorized"}, 401)

            handlers = self.get_request_handlers()
            result = handlers.handle_get_verified_senders(user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_imap_config_post(self):
            """Handle /api/imap/config POST endpoint."""
            payload = self._read_json(default={})

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            handlers = self.get_request_handlers()
            result = handlers.handle_imap_config_save(user_id=user_id, payload=payload)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_imap_test_post(self):
            """Handle /api/imap/test POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            handlers = self.get_request_handlers()
            result = handlers.handle_imap_test(user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_document_extract_rfp_post(self):
            """Handle /api/document/extract-rfp POST endpoint."""
            payload = self._read_json(default={})

            auth_header = self.headers.get('Authorization', '')
            print(f"[RAG] Document extract-rfp - Auth header: {auth_header[:50] if auth_header else 'None'}")

            user_data = self._require_auth(auth_header=auth_header)
            print(f"[RAG] Document extract-rfp - Token valid: {bool(user_data)}")
            if user_data is None:
                print(f"[RAG] Document extract-rfp - Auth failed")
                return

            user_id = user_data.get('id') if user_data else None
            document_id = payload.get('document_id')

            if not document_id:
                return self.json({"error": "Missing document_id parameter"}, 400)

            handlers = self.get_request_handlers()
            result = handlers.handle_extract_rfp_from_document(document_id=document_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_document_update_content_post(self):
            """Handle /api/document/update-content POST endpoint."""
            payload = self._read_json(default={})

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            document_id = payload.get('document_id')
            content = payload.get('content', '')

            if not document_id:
                return self.json({"error": "Missing document_id parameter"}, 400)

            handlers = self.get_request_handlers()
            result = handlers.handle_update_document_content(
                document_id=document_id,
                content=content,
                user_id=user_id
            )
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_send_quote_for_opportunity_post(self, send_quote_match):
            """Handle /api/opportunity/{id}/send-quote POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            opportunity_id = send_quote_match.group(1)

            payload = self._read_json_or_error()
            if payload is None:
                return

            handlers = self.get_request_handlers()
            result = handlers.handle_send_quote_for_opportunity(
                opportunity_id=opportunity_id,
                payload=payload,
                user_id=user_id,
            )
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_chat_attachments_post(self, parsed):
            """Handle /api/chat/attachments POST endpoint."""
            body = self._read_body()
            content_type = self.headers.get('Content-Type', '')

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            qs = urllib.parse.parse_qs(parsed.query)
            opportunity_id = qs.get('opportunity_id', [None])[0]

            handlers = self.get_request_handlers()
            result = handlers.handle_chat_attachment_upload(
                body=body,
                content_type=content_type,
                user_id=user_id,
                opportunity_id=opportunity_id,
            )
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunity_rfq_generate_post(self, opp_match):
            """Handle /api/opportunity/{id}/rfq/generate POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            opportunity_id = opp_match.group(1)
            handlers = self.get_request_handlers()
            print(f"[RAG] Generating quote for opportunity {opportunity_id} by user {user_id}")
            result = handlers.handle_generate_quote_for_opportunity(
                opportunity_id=opportunity_id,
                user_id=user_id,
            )
            print('result:', result)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_opportunity_rfq_create_from_text_post(self, opp_rfq_create_match):
            """Handle /api/opportunity/{id}/rfq/create-from-text POST endpoint."""
            body = self._read_body()
            content_type = self.headers.get('Content-Type', '')

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            handlers = self.get_request_handlers()
            opportunity_id = opp_rfq_create_match.group(1)

            if opportunity_id == "new":
                result = handlers.handle_create_opportunity_from_rfp(
                    body=body,
                    content_type=content_type,
                    user_id=user_id
                )
                if result.get('status') == 'ok':
                    opportunity = result.get('opportunity', {})
                    opportunity_id = opportunity.get('id')
                    print(f"[BusinessHandlers] Generating quote for opportunity {opportunity_id} by user")
                    handlers.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id, user_id=user_id)
            else:
                result = handlers.handle_create_rfq_source_from_html_body(
                    opportunity_id=opportunity_id,
                    body=body,
                    content_type=content_type,
                    user_id=user_id
                )

            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_quote_pdf_post(self, quote_pdf_match):
            """Handle /api/quote/{id}/pdf POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            document_id = quote_pdf_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_generate_quote_pdf(document_id=document_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_quote_invoice_post(self, quote_invoice_match):
            """Handle /api/quote/{id}/invoice POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            quote_id = quote_invoice_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_generate_invoice_from_quote(quote_id=quote_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_invoice_pdf_post(self, invoice_pdf_match):
            """Handle /api/invoice/{id}/pdf POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            invoice_id = invoice_pdf_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_invoice_send_post(self, invoice_send_match):
            """Handle /api/invoice/{id}/send POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            invoice_id = invoice_send_match.group(1)

            payload = self._read_json_or_error()
            if payload is None:
                return

            handlers = self.get_request_handlers()
            result = handlers.handle_send_invoice(invoice_id=invoice_id, payload=payload, user_id=user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_quote_update_post(self, quote_update_match):
            """Handle /api/quote/{id} POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            document_id = quote_update_match.group(1)
            payload = self._read_json(default={})

            print(f"[RAG] Updating quote {document_id} by user {user_id} with payload: {payload}")
            handlers = self.get_request_handlers()
            result = handlers.handle_update_quote(document_id=document_id, payload=payload, user_id=user_id)
            status = self._status_from_error(result)
            return self.json(result, status)

        def _handle_quote_submit_post(self):
            """Handle /api/quote POST endpoint."""
            content_type = self.headers.get('Content-Type', '')
            body = self._read_body()
            handlers = self.get_request_handlers()
            result = handlers.handle_quote_submit(body, content_type)
            return self.json(result)

        def _handle_quote_send_post(self):
            """Handle /api/quote/send POST endpoint."""
            print(f"[RAG] Received request to send quote email, path: /api/quote/send, method: {self.command}")
            content_type = self.headers.get('Content-Type', '')
            body = self._read_body()

            handlers = self.get_request_handlers()
            result = handlers.handle_quote_send(body, content_type)
            return self.json(result)

        def _handle_csv_source_post(self):
            """Handle /api/csv/source POST endpoint."""
            content_type = self.headers.get('Content-Type', '')
            body = self._read_body()
            content_length = len(body)

            handlers = self.get_request_handlers()
            result = handlers.handle_csv_source_upload(content_type, content_length, body)
            return self.json(result)

        def _handle_rfp_post(self):
            """Handle /api/rfp POST endpoint."""
            content_type = self.headers.get('Content-Type', '')
            body = self._read_body()

            handlers = self.get_request_handlers()
            result = handlers.handle_rfp_upload(body, content_type)
            return self.json(result)

        def _handle_actions_create_post(self):
            """Handle /api/actions POST endpoint."""
            data = self._read_json_or_error()
            if data is None:
                return

            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None

            handlers = self.get_request_handlers()
            result = handlers.handle_create_action(data, user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_action_pause_post(self, pause_action_match):
            """Handle /api/actions/{id}/pause POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            action_id = pause_action_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_pause_action(action_id, user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_action_resume_post(self, resume_action_match):
            """Handle /api/actions/{id}/resume POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            action_id = resume_action_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_resume_action(action_id, user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_action_execute_post(self, execute_action_match):
            """Handle /api/actions/{id}/execute POST endpoint."""
            user_data = self._require_auth()
            if user_data is None:
                return

            user_id = user_data.get('id') if user_data else None
            action_id = execute_action_match.group(1)

            handlers = self.get_request_handlers()
            result = handlers.handle_execute_action(action_id, user_id)
            status = self._status_from_result(result)
            return self.json(result, status)

        def _handle_products_get(self, qs):
            """Handle /api/products GET endpoint."""
            return handle_products_get(self, qs)

        def _handle_google_oauth_callback_get(self, qs):
            """Handle Google OAuth callback route."""
            return handle_google_oauth_callback_get(self, qs)

        def _handle_email_fetch_loop_status_get(self):
            """Handle /api/email-fetch-loop/status GET endpoint."""
            return handle_email_fetch_loop_status_get(self, __file__)

        def _handle_auth_user_get(self):
            """Handle /api/auth/user GET endpoint."""
            return handle_auth_user_get(self)

        def _handle_oauth_login_get(self, qs):
            """Handle /api/oauth/login GET endpoint."""
            return handle_oauth_login_get(self, qs)

        def _handle_oauth_callback_get(self, qs):
            """Handle /api/oauth/callback GET endpoint."""
            return handle_oauth_callback_get(self, qs)

        def _handle_fetch_get(self, qs):
            """Handle /api/fetch GET endpoint."""
            return handle_fetch_get(self, qs)

        def _handle_gmail_status_get(self, qs):
            """Handle /api/gmail/status GET endpoint."""
            return handle_gmail_status_get(self, qs)

        def _handle_gmail_authorize_get(self, qs):
            """Handle /api/gmail/authorize GET endpoint."""
            return handle_gmail_authorize_get(self, qs)

        def _handle_gmail_oauth_start_get(self, qs):
            """Handle /api/gmail/oauth/start GET endpoint."""
            return handle_gmail_oauth_start_get(self, qs)

        def _handle_gmail_revoke_get(self, qs):
            """Handle /api/gmail/revoke GET endpoint."""
            return handle_gmail_revoke_get(self, qs)

        def _handle_gmail_profile_get(self, qs):
            """Handle /api/gmail/profile GET endpoint."""
            return handle_gmail_profile_get(self, qs)

        def _handle_imap_status_get(self):
            """Handle /api/imap/status GET endpoint."""
            return handle_imap_status_get(self)

        def _handle_imap_config_get(self):
            """Handle /api/imap/config GET endpoint."""
            return handle_imap_config_get(self)

        def _handle_gmail_messages_get(self, qs):
            """Handle /api/gmail/messages GET endpoint."""
            return handle_gmail_messages_get(self, qs)

        def _handle_gmail_classify_unclassified_get(self, qs):
            """Handle /api/gmail/classify-unclassified GET endpoint."""
            return handle_gmail_classify_unclassified_get(self, qs)

        def _handle_gmail_message_get(self, parsed_path: str):
            """Handle /api/gmail/message/<id> GET endpoint."""
            return handle_gmail_message_get(self, parsed_path)

        def _handle_email_attachment_get(self, parsed_path: str):
            """Handle /api/email-attachment/<id> GET endpoint."""
            return handle_email_attachment_get(self, parsed_path)

        def _handle_opportunities_search_get(self, qs, handlers):
            """Handle /api/opportunities/search GET endpoint."""
            return handle_opportunities_search_get(self, qs, handlers)

        def _handle_opportunity_actions_list_get(self, list_actions_match, handlers):
            """Handle /api/opportunities/<id>/actions GET endpoint."""
            return handle_opportunity_actions_list_get(self, list_actions_match, handlers)

        def _handle_action_get(self, get_action_match, handlers):
            """Handle /api/actions/<id> GET endpoint."""
            return handle_action_get(self, get_action_match, handlers)

        def _handle_action_logs_get(self, get_action_logs_match, qs, handlers):
            """Handle /api/actions/<id>/logs GET endpoint."""
            return handle_action_logs_get(self, get_action_logs_match, qs, handlers)

        def _handle_quotes_download_get(self, parsed_path: str, qs, handlers):
            """Handle /api/quotes/download/<filename> GET endpoint."""
            return handle_quotes_download_get(self, parsed_path, qs, handlers)

        def _handle_documents_download_get(self, parsed_path: str, qs, handlers):
            """Handle /api/documents/download/<filename> GET endpoint."""
            return handle_documents_download_get(self, parsed_path, qs, handlers)

        def _handle_csv_get(self, parsed_path: str, qs):
            """Handle /api/csv* GET endpoints."""
            return handle_csv_get(self, parsed_path, qs)

        def _handle_csv_files_get(self, qs, handlers):
            """Handle /api/csv/files GET endpoint."""
            return handle_csv_files_get(self, qs, handlers)

        def _handle_csv_preview_get(self, qs, handlers):
            """Handle /api/csv/preview GET endpoint."""
            return handle_csv_preview_get(self, qs, handlers)

        def _handle_csv_sources_get(self, handlers):
            """Handle /api/csv/sources GET endpoint."""
            return handle_csv_sources_get(self, handlers)

        def _handle_csv_query_get(self, qs, handlers):
            """Handle /api/csv/query GET endpoint."""
            return handle_csv_query_get(self, qs, handlers)

        def _handle_csv_search_get(self, qs, handlers):
            """Handle /api/csv/search* GET endpoints."""
            return handle_csv_search_get(self, qs, handlers)

        def _handle_quotes_list_get(self, handlers):
            """Handle /api/quotes/list GET endpoint."""
            return handle_quotes_list_get(self, handlers)

        def _get_qs_int(self, qs, key: str, default: int) -> int:
            """Read integer query-string parameter with fallback."""
            return get_qs_int(qs, key=key, default=default)

        def _get_qs_value(self, qs, key: str, default=None):
            """Read first query-string value with fallback."""
            return get_qs_value(qs, key=key, default=default)

        def _get_payload_int(self, payload: Dict, key: str, default: int) -> int:
            """Read integer payload value with fallback."""
            return get_payload_int(payload, key=key, default=default)

        def _get_optional_user_id_from_auth(self, auth_header: str):
            """Extract user id from auth header without enforcing auth."""
            return get_optional_user_id_from_auth(self, auth_header)

        def _require_auth_user_id(self):
            """Require authenticated user and return its id."""
            return require_auth_user_id(self)

        def _get_qs_bool(self, qs, key: str, default: bool = False) -> bool:
            """Read boolean query-string parameter with fallback."""
            return get_qs_bool(qs, key=key, default=default)

        def _handle_prompt_get(self, parsed_path: str):
            """Handle GET requests for prompt markdown content."""
            return handle_prompt_get(self, parsed_path, __file__)

        def authorize(self) -> Dict:
            return authorize_request(self)

        def _require_auth(self, auth_header: str = None, required: bool = True) -> Dict:
            return require_auth(self, auth_header=auth_header, required=required)

        def _read_body(self) -> bytes:
            return read_body(self)

        def _read_json(self, default=None):
            return read_json(self, default=default)

        def _read_json_or_error(self, error_payload=None, status_code=400):
            return read_json_or_error(self, error_payload=error_payload, status_code=status_code)

        def _resolve_fs_path(self, raw_path: str):
            return resolve_fs_path(self, current_file=__file__, raw_path=raw_path)
        
        def _handle_raw_stream(self, qs, handlers):
            """Stream raw CSV file."""
            return handle_raw_stream(self, qs, handlers)

        def _handle_csv_download(self, qs, handlers):
            """Download CSV file with proper filename."""
            return handle_csv_download(self, qs, handlers)

        def _handle_source_stream(self, qs, handlers):
            """Stream original Excel source file."""
            return handle_source_stream(self, qs, handlers)

        def _handle_quote_download(self, filename, handlers, qs=None):
            """Stream PDF quote file."""
            return handle_quote_download(self, filename, handlers, qs)

        def _handle_document_download(self, filename, handlers, qs=None):
            """Stream document file (PDF, DOCX, etc.)."""
            return handle_document_download(self, filename, handlers, qs)

        def json(self, payload, status_code=200):
            """Send JSON response."""
            return send_json(self, payload, status_code=status_code)

        def _send_error(self, code: int, message: str):
            """Send error response."""
            return send_error(self, code=code, message=message)

        def _send_text_response(self, code: int, content_type: str, body: bytes = None):
            """Send plain text/binary response payload."""
            return send_text_response(self, code=code, content_type=content_type, body=body)

        def _send_redirect(self, location: str, code: int = 302):
            """Send HTTP redirect response."""
            return send_redirect(self, location=location, code=code)
    
    return Rag


# Backward-compatible alias used by integration tests and legacy callers.
make_handler = create_rag_handler


def main():
    if not config["STORAGE_DIR"].exists():
        print(f"Storage directory not found: {config['STORAGE_DIR']}")
        sys.exit(1)
    
    # Test LLM connection (non-blocking)
    test_llm_connection()
    
    try:
        signal.signal(signal.SIGTERM, lambda s, f: (_ for _ in ()).throw(KeyboardInterrupt()))
    except Exception:
        pass

    Handler = create_rag_handler(config)
    with ReusableThreadingHTTPServer(('', config["PORT"]), Handler) as httpd:
        print(f"CSV server on http://127.0.0.1:{config['PORT']}")
        print(f"Storage dir: {config['STORAGE_DIR']}")
        print(f"ex: http://127.0.0.1:{config['PORT']}/api/csv/sources")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            try:
                httpd.shutdown()
            except Exception:
                pass
            httpd.server_close()


if __name__ == '__main__':
    main()
