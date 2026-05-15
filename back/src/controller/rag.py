#!/usr/bin/env python3
"""
Quote Management.s
Config via env:
- PORT (default 8088)
- STORAGE_DIR (default ./var/storage)
"""
import os
import sys
import json
import re
import urllib.parse
import urllib.request
import http.server
import signal
import socket
import traceback
from pathlib import Path

from typing import Dict
from src.config import EMAIL_FETCH_MAX_RESULTS
from src.reader.csv import CSVReader
from src.embeddings import EmbeddingGenerator
from src.controller.file_handler import FileHandler
from src.controller.handlers import RequestHandlers
from src.controller.auth.auth_handler import AuthHandler
from src.controller.llm_factory import LLMClientFactory
from src.api.routes.ddd_get_routes import handle_ddd_get_route, is_ddd_get_route
from src.api.routes.ddd_post_routes import handle_ddd_post_route, is_ddd_post_route

# Load .env before reading config values
try:
    from dotenv import load_dotenv, find_dotenv, dotenv_values
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)
        print(f"[dotenv] Loaded from {env_file}")

    # Optional: load shared Supabase env (single source of truth)
    shared_env_rel = os.environ.get("SUPABASE_ENV_FILE", "../supabase/.env.prod")
    shared_env_path = Path(shared_env_rel)
    if not shared_env_path.is_absolute():
        base_dir = Path(env_file).parent if env_file else Path(__file__).resolve().parents[2]
        shared_env_path = (base_dir / shared_env_path).resolve()

    if shared_env_path.exists():
        shared_env = dotenv_values(shared_env_path)
        os.environ["SUPABASE_URL"] = (
            shared_env.get("SUPABASE_PUBLIC_URL")
            or shared_env.get("API_EXTERNAL_URL")
            or shared_env.get("SITE_URL")
            or os.environ.get("SUPABASE_URL", "")
        )
        os.environ["SUPABASE_ANON_KEY"] = shared_env.get("ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
        os.environ["SUPABASE_SERVICE_KEY"] = shared_env.get("SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY", "")
except Exception:
    pass


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

                if self._handle_delete_routes(parsed.path):
                    return
                
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return self._send_error(500, f"Server error: {str(e)}")

        def _handle_delete_routes(self, parsed_path: str) -> bool:
            """Handle DELETE routes."""
            opportunity_delete_match = re.match(r"^/api/opportunities/([^/]+)$", parsed_path)
            if opportunity_delete_match:
                self._handle_opportunity_delete(opportunity_delete_match)
                return True

            quote_delete_match = re.match(r"^/api/quote/([^/]+)$", parsed_path)
            if quote_delete_match:
                self._handle_quote_delete(quote_delete_match)
                return True

            document_delete_match = re.match(r"^/api/document/([^/]+)$", parsed_path)
            if document_delete_match:
                self._handle_document_delete(document_delete_match)
                return True

            attachment_delete_match = re.match(r"^/api/email-attachment/([^/]+)$", parsed_path)
            if attachment_delete_match:
                self._handle_email_attachment_delete(attachment_delete_match)
                return True

            email_delete_match = re.match(r"^/api/email/([^/]+)$", parsed_path)
            if email_delete_match:
                self._handle_email_delete(email_delete_match)
                return True

            action_delete_match = re.match(r"^/api/actions/([^/]+)$", parsed_path)
            if action_delete_match:
                self._handle_action_delete(action_delete_match)
                return True

            if parsed_path == '/api/imap/config':
                self._handle_imap_config_delete()
                return True

            return False

        def do_PATCH(self):
            try:
                parsed = urllib.parse.urlparse(self.path)
                print(f"[RAG] PATCH request to: {parsed.path}")
                if self._handle_patch_routes(parsed.path):
                    return

                print(f"[RAG] PATCH path not matched: {parsed.path}")
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] PATCH error: {e}")
                return self._send_error(500, f"Server error: {str(e)}")

        def _handle_patch_routes(self, _parsed_path: str) -> bool:
            """Handle PATCH routes."""
            return False

        def do_PUT(self):
            try:
                parsed = urllib.parse.urlparse(self.path)

                if self._handle_put_routes(parsed.path):
                    return
                
                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                return self._send_error(500, f"Server error: {str(e)}")

        def _handle_put_routes(self, parsed_path: str) -> bool:
            """Handle PUT routes."""
            update_action_match = re.match(r"^/api/actions/([^/]+)$", parsed_path)
            if update_action_match:
                self._handle_action_update_put(update_action_match)
                return True

            return False

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
            return ok if result.get('status') == 'ok' else error

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

                if self._handle_ddd_post_routes(parsed):
                    return

                if self._handle_post_core_routes(parsed.path):
                    return
                
                if self._handle_post_auth_routes(parsed.path):
                    return
                
                if self._handle_post_domain_routes(parsed):
                    return

                if self._handle_post_opportunity_quote_invoice_routes(parsed):
                    return
                
                if self._handle_post_legacy_and_action_routes(parsed.path):
                    return

                return self._send_error(404, "Not found")
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling request: {e}")
                
                return self._send_error(500, f"Internal server error 1: {e}")

        def do_HEAD(self):
            try:
                parsed = urllib.parse.urlparse(self.path)

                if parsed.path.startswith('/api/storage/'):
                    return self._handle_storage_head(parsed.path)

                return self._send_error(404, "Not found")
            except Exception as e:
                return self._send_error(500, f"Internal server error 2: {e}")

        def _handle_storage_head(self, parsed_path: str):
            """Handle HEAD requests for storage files."""
            raw_filename = parsed_path[len('/api/storage/'):]
            handlers = self.get_request_handlers()
            try:
                storage_info = handlers.handle_storage_resolve_file(config['STORAGE_DIR'], raw_filename)
            except FileNotFoundError:
                not_found = handlers.handle_storage_not_found_payload(raw_filename, include_body=False)
                print(f"[RAG] File not found in any storage location: {not_found['filename']}")
                self._send_text_response(404, not_found['content_type'])
                return

            filename = storage_info['filename']
            metadata = storage_info['metadata']

            print(f"[RAG] Storage HEAD request for file: {filename}")
            response_headers = handlers.handle_storage_response_headers(metadata)

            self.send_response(200)
            for header_name, header_value in response_headers.items():
                self.send_header(header_name, header_value)
            self.end_headers()

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

                if self._handle_ddd_get_routes(parsed, qs):
                    return

                if parsed.path == '/api/products':
                    return self._handle_products_get(qs)

                if parsed.path.startswith('/api/google/oauth/callback'):
                    return self._handle_google_oauth_callback_get(qs)

                # Prompt endpoint: /api/prompt/<relative_path> -> back/src/prompt/<relative_path>/prompt.md
                if parsed.path.startswith('/api/prompt/'):
                    return self._handle_prompt_get(parsed.path)

                if parsed.path == '/api/fetch':
                    return self._handle_fetch_get(qs)

                if parsed.path == '/api/email-fetch-loop/status':
                    return self._handle_email_fetch_loop_status_get()
                
                # Storage endpoint for serving uploaded files
                if parsed.path.startswith('/api/storage/'):
                    return self._handle_storage_get(parsed.path)
                
                # Auth endpoint
                if parsed.path == '/api/auth/user':
                    return self._handle_auth_user_get()
                
                # Existing endpoints
                if parsed.path == '/api/gmail/oauth/start':
                    return self._handle_gmail_oauth_start_get(qs)
                if parsed.path == '/api/gmail/authorize':
                    return self._handle_gmail_authorize_get(qs)
                elif parsed.path == '/api/gmail/status':
                    return self._handle_gmail_status_get(qs)
                elif parsed.path == '/api/gmail/revoke':
                    return self._handle_gmail_revoke_get(qs)
                elif parsed.path == '/api/gmail/profile':
                    return self._handle_gmail_profile_get(qs)
                elif parsed.path == '/api/imap/status':
                    return self._handle_imap_status_get()
                elif parsed.path == '/api/imap/config':
                    return self._handle_imap_config_get()
                elif parsed.path == '/api/gmail/messages':
                    return self._handle_gmail_messages_get(qs)
                elif parsed.path == '/api/gmail/classify-unclassified':
                    return self._handle_gmail_classify_unclassified_get(qs)
                elif parsed.path.startswith('/api/gmail/message/'):
                    return self._handle_gmail_message_get(parsed.path)
                elif parsed.path.startswith('/api/email-attachment/'):
                    return self._handle_email_attachment_get(parsed.path)
                if parsed.path.startswith('/api/csv'):
                    return self._handle_csv_get(parsed.path, qs)

                handlers = self.get_request_handlers()
                if parsed.path == '/api/quotes/list':
                    return self._handle_quotes_list_get(handlers)
                if parsed.path == '/api/opportunities/search':
                    return self._handle_opportunities_search_get(qs, handlers)
                
                # Action endpoints - List actions for opportunity
                list_actions_match = re.match(r"^/api/opportunities/([^/]+)/actions$", parsed.path)
                if list_actions_match:
                    return self._handle_opportunity_actions_list_get(list_actions_match, handlers)
                
                # Get action details
                get_action_match = re.match(r"^/api/actions/([^/]+)$", parsed.path)
                if get_action_match:
                    return self._handle_action_get(get_action_match, handlers)
                
                # Get action logs
                get_action_logs_match = re.match(r"^/api/actions/([^/]+)/logs$", parsed.path)
                if get_action_logs_match:
                    return self._handle_action_logs_get(get_action_logs_match, qs, handlers)
                
                if parsed.path.startswith('/api/quotes/download/'):
                    return self._handle_quotes_download_get(parsed.path, qs, handlers)
                if parsed.path.startswith('/api/documents/download/'):
                    return self._handle_documents_download_get(parsed.path, qs, handlers)
                else:
                    # Fallback to static file serving
                    return super().do_GET()
            except Exception as e:
                traceback.print_exc()
                print(f"[RAG] Error handling GET request: {e}")

                return self._send_error(500, f"Internal server error 3: {e}")

        def _handle_storage_get(self, parsed_path: str):
            """Handle GET requests for storage files."""
            raw_filename = parsed_path[len('/api/storage/'):]
            handlers = self.get_request_handlers()
            try:
                storage_info = handlers.handle_storage_resolve_file(config['STORAGE_DIR'], raw_filename)
            except FileNotFoundError:
                not_found = handlers.handle_storage_not_found_payload(raw_filename, include_body=True)
                print(f"[RAG] Storage request for file: {not_found['filename']}")
                print(f"[RAG] File not found in any storage location: {not_found['filename']}")
                self._send_text_response(404, not_found['content_type'], not_found['body'])
                return

            filename = storage_info['filename']
            storage_path = storage_info['storage_path']
            metadata = storage_info['metadata']

            print(f"[RAG] Storage request for file: {filename}")

            try:
                print(f"[RAG] Reading file: {storage_path}")
                response_headers = handlers.handle_storage_response_headers(metadata)

                self.send_response(200)
                for header_name, header_value in response_headers.items():
                    self.send_header(header_name, header_value)
                self.end_headers()

                # Stream file to avoid truncation issues
                for chunk in handlers.handle_storage_read_chunks(storage_path):
                    self.wfile.write(chunk)
                print(f"[RAG] File sent successfully: {filename} ({metadata['file_size']} bytes)")
                return
            except Exception as e:
                print(f"[RAG] Error reading file {filename}: {e}")
                traceback.print_exc()
                error_payload = handlers.handle_storage_read_error_payload(e)
                self._send_text_response(500, error_payload['content_type'], error_payload['body'])
                return

        def _handle_post_opportunity_quote_invoice_routes(self, parsed):
            """Handle secondary POST routes for opportunity/quote/invoice flows."""
            send_quote_match = re.match(r"^/api/opportunity/([^/]+)/send-quote$", parsed.path)
            if send_quote_match:
                self._handle_send_quote_for_opportunity_post(send_quote_match)
                return True

            if parsed.path == '/api/chat/attachments':
                self._handle_chat_attachments_post(parsed)
                return True

            opp_match = re.match(r"^/api/opportunity/([^/]+)/rfq/generate$", parsed.path)
            if opp_match:
                self._handle_opportunity_rfq_generate_post(opp_match)
                return True

            opp_rfq_create_match = re.match(r"^/api/opportunity/([^/]+)/rfq/create-from-text$", parsed.path)
            if opp_rfq_create_match:
                self._handle_opportunity_rfq_create_from_text_post(opp_rfq_create_match)
                return True

            quote_pdf_match = re.match(r"^/api/quote/([^/]+)/pdf$", parsed.path)
            if quote_pdf_match:
                self._handle_quote_pdf_post(quote_pdf_match)
                return True

            quote_invoice_match = re.match(r"^/api/quote/([^/]+)/invoice$", parsed.path)
            if quote_invoice_match:
                self._handle_quote_invoice_post(quote_invoice_match)
                return True

            invoice_pdf_match = re.match(r"^/api/invoice/([^/]+)/pdf$", parsed.path)
            if invoice_pdf_match:
                self._handle_invoice_pdf_post(invoice_pdf_match)
                return True

            invoice_send_match = re.match(r"^/api/invoice/([^/]+)/send$", parsed.path)
            if invoice_send_match:
                self._handle_invoice_send_post(invoice_send_match)
                return True

            quote_update_match = re.match(r"^/api/quote/([^/]+)$", parsed.path)
            if quote_update_match:
                self._handle_quote_update_post(quote_update_match)
                return True

            return False

        def _handle_post_core_routes(self, parsed_path: str) -> bool:
            """Handle core POST routes that map directly to controller helpers."""
            if parsed_path == '/api/products':
                self._handle_products_post()
                return True

            if parsed_path == '/api/fs/create':
                self._handle_fs_create_post()
                return True

            if parsed_path == '/api/fs/read':
                self._handle_fs_read_post()
                return True

            if parsed_path == '/api/curl':
                self._handle_curl_post()
                return True

            return False

        def _handle_post_auth_routes(self, parsed_path: str) -> bool:
            """Handle auth POST routes."""
            if parsed_path == '/api/auth/signup':
                self._handle_auth_signup_post()
                return True

            if parsed_path == '/api/auth/login':
                self._handle_auth_login_post()
                return True

            if parsed_path == '/api/auth/logout':
                self._handle_auth_logout_post()
                return True

            return False

        def _handle_post_domain_routes(self, parsed) -> bool:
            """Handle entity/email/opportunity/imap/document POST routes."""
            parsed_path = parsed.path
            entity_update_match = re.match(r"^/api/entity/([^/]+)/([^/]+)$", parsed_path)
            if entity_update_match:
                self._handle_entity_update_post(entity_update_match)
                return True

            if parsed_path.startswith('/api/emails/classify/'):
                self._handle_emails_classify_post(parsed_path)
                return True

            if parsed_path == '/api/rfq/generate':
                self._handle_rfq_generate_post()
                return True

            if parsed_path == '/api/opportunities/create-from-email':
                self._handle_opportunities_create_from_email_post()
                return True

            if parsed_path == '/api/opportunities/create-manual':
                self._handle_opportunities_create_manual_post()
                return True

            if parsed_path == '/api/opportunities/create-from-rfp':
                self._handle_opportunities_create_from_rfp_post()
                return True

            if parsed_path == '/api/email/extract-contact':
                self._handle_email_extract_contact_post()
                return True

            if parsed_path.startswith('/api/email/auth/'):
                self._handle_email_auth_status_post(parsed_path)
                return True

            if parsed_path.startswith('/api/email/') and parsed_path.endswith('/resync'):
                self._handle_email_resync_post(parsed_path)
                return True

            if parsed_path == '/api/email/senders/high-risk':
                self._handle_email_senders_high_risk_post()
                return True

            if parsed_path == '/api/email/senders/verified':
                self._handle_email_senders_verified_post()
                return True

            if parsed_path == '/api/imap/config':
                self._handle_imap_config_post()
                return True

            if parsed_path == '/api/imap/test':
                self._handle_imap_test_post()
                return True

            if parsed_path == '/api/document/extract-rfp':
                self._handle_document_extract_rfp_post()
                return True

            if parsed_path == '/api/document/update-content':
                self._handle_document_update_content_post()
                return True

            return False

        def _handle_action_post_routes(self, parsed_path: str) -> bool:
            """Handle action-specific POST regex routes."""
            pause_action_match = re.match(r"^/api/actions/([^/]+)/pause$", parsed_path)
            if pause_action_match:
                self._handle_action_pause_post(pause_action_match)
                return True

            resume_action_match = re.match(r"^/api/actions/([^/]+)/resume$", parsed_path)
            if resume_action_match:
                self._handle_action_resume_post(resume_action_match)
                return True

            execute_action_match = re.match(r"^/api/actions/([^/]+)/execute$", parsed_path)
            if execute_action_match:
                self._handle_action_execute_post(execute_action_match)
                return True

            return False

        def _handle_post_legacy_and_action_routes(self, parsed_path: str) -> bool:
            """Handle remaining legacy and action POST routes."""
            if parsed_path == '/api/csv/source':
                self._handle_csv_source_post()
                return True

            if parsed_path == '/api/rfp':
                self._handle_rfp_post()
                return True

            if parsed_path == '/api/quote':
                self._handle_quote_submit_post()
                return True

            if parsed_path == '/api/quote/send':
                self._handle_quote_send_post()
                return True

            if parsed_path == '/api/actions':
                self._handle_actions_create_post()
                return True

            return self._handle_action_post_routes(parsed_path)

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
            status = result.pop('status', 200)
            return self.json(result, status)

        def _handle_auth_login_post(self):
            """Handle /api/auth/login POST endpoint."""
            body = self._read_body()
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_login(body)
            status = result.pop('status', 200)
            return self.json(result, status)

        def _handle_auth_logout_post(self):
            """Handle /api/auth/logout POST endpoint."""
            auth_header = self.headers.get('Authorization', '')
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_logout(auth_header)
            status = result.pop('status', 200)
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
            status = 400 if result.get('error') else 200
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
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_products_get(self, qs):
            """Handle /api/products GET endpoint."""
            handlers = self.get_request_handlers()
            return self.json(handlers.handle_list_products(qs))

        def _handle_google_oauth_callback_get(self, qs):
            """Handle Google OAuth callback route."""
            handlers = self.get_request_handlers()
            code = qs.get('code', [None])[0]
            state = qs.get('state', [None])[0]
            if not code:
                return self._send_error(400, 'Missing code parameter')

            result = handlers.handle_gmail_oauth_callback(code, state)
            if result.get('status') == 'ok':
                redirect_url = result.get('redirect_url') or 'http://localhost:5173/settings'
                return self._send_redirect(redirect_url)

            return self.json(result, 500)

        def _handle_email_fetch_loop_status_get(self):
            """Handle /api/email-fetch-loop/status GET endpoint."""
            status_path = Path(__file__).resolve().parents[3] / 'var' / 'email_fetch_loop.json'
            legacy_path = Path(__file__).resolve().parents[2] / 'var' / 'email_fetch_loop.json'
            handlers = self.get_request_handlers()
            result = handlers.handle_email_fetch_loop_status(status_path=status_path, legacy_path=legacy_path)
            return self.json(result)

        def _handle_auth_user_get(self):
            """Handle /api/auth/user GET endpoint."""
            auth_header = self.headers.get('Authorization', '')
            handlers = self.get_request_handlers()
            result = handlers.handle_auth_user(auth_header)
            status = result.pop('status', 200)
            return self.json(result, status)

        def _handle_fetch_get(self, qs):
            """Handle /api/fetch GET endpoint."""
            target_url = qs.get('url', [None])[0]
            if not target_url:
                return self._send_error(400, 'Missing url parameter')

            if not target_url.startswith('http://') and not target_url.startswith('https://'):
                return self._send_error(400, 'Invalid url scheme')

            max_chars = self._get_qs_int(qs, 'max_chars', 10000)
            timeout_ms = self._get_qs_int(qs, 'timeout_ms', 8000)

            max_chars = max(100, min(max_chars, 50000))
            timeout_ms = max(1000, min(timeout_ms, 20000))

            try:
                handlers = self.get_request_handlers()
                result = handlers.handle_fetch_url(
                    target_url=target_url,
                    max_chars=max_chars,
                    timeout_ms=timeout_ms,
                )
                return self.json(result)
            except Exception as e:
                return self._send_error(500, f'Fetch failed: {e}')

        def _handle_gmail_status_get(self, qs):
            """Handle /api/gmail/status GET endpoint."""
            handlers = self.get_request_handlers()
            user_id = self._get_qs_value(qs, 'user_id')
            result = handlers.handle_gmail_status(user_id=user_id)
            return self.json(result)

        def _handle_gmail_authorize_get(self, qs):
            """Handle /api/gmail/authorize GET endpoint."""
            handlers = self.get_request_handlers()
            redirect_url = self._get_qs_value(qs, 'redirect_url')
            result = handlers.handle_gmail_authorize(redirect_url)
            return self.json(result)

        def _handle_gmail_oauth_start_get(self, qs):
            """Handle /api/gmail/oauth/start GET endpoint."""
            handlers = self.get_request_handlers()
            redirect_url = self._get_qs_value(qs, 'redirect_url')
            user_id = self._get_qs_value(qs, 'user_id')
            result = handlers.handle_gmail_oauth_start(redirect_url, user_id=user_id)
            return self.json(result)

        def _handle_gmail_revoke_get(self, qs):
            """Handle /api/gmail/revoke GET endpoint."""
            handlers = self.get_request_handlers()
            user_id = self._get_qs_value(qs, 'user_id')
            result = handlers.handle_gmail_revoke(user_id=user_id)
            return self.json(result)

        def _handle_gmail_profile_get(self, qs):
            """Handle /api/gmail/profile GET endpoint."""
            handlers = self.get_request_handlers()
            user_id = self._get_qs_value(qs, 'user_id')
            result = handlers.handle_gmail_profile(user_id=user_id)
            return self.json(result)

        def _handle_imap_status_get(self):
            """Handle /api/imap/status GET endpoint."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return
            handlers = self.get_request_handlers()
            result = handlers.handle_imap_status(user_id=user_id)
            return self.json(result)

        def _handle_imap_config_get(self):
            """Handle /api/imap/config GET endpoint."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return
            handlers = self.get_request_handlers()
            result = handlers.handle_imap_config(user_id=user_id)
            return self.json(result)

        def _handle_gmail_messages_get(self, qs):
            """Handle /api/gmail/messages GET endpoint."""
            handlers = self.get_request_handlers()
            max_results = self._get_qs_int(qs, 'max_results', EMAIL_FETCH_MAX_RESULTS)
            user_id = qs.get('user_id', [None])[0]
            force = self._get_qs_bool(qs, 'force', False)

            print(f"[RAG] /api/gmail/messages - user_id from query: {user_id}, force: {force}")

            if not user_id:
                auth_header = self.headers.get('Authorization', '')
                print(f"[RAG] Auth header: {auth_header[:50] if auth_header else 'None'}...")
                user_id = self._get_optional_user_id_from_auth(auth_header)
                print(f"[RAG] Extracted user_id from token: {user_id}")

            print(f"[RAG] Final user_id: {user_id}")
            if not user_id:
                return self._send_error(400, 'Missing user_id')

            result = handlers.handle_gmail_list_messages(
                max_results=max_results,
                user_id=user_id,
                save_to_db=True,
                force=force,
            )
            return self.json(result)

        def _handle_gmail_classify_unclassified_get(self, qs):
            """Handle /api/gmail/classify-unclassified GET endpoint."""
            handlers = self.get_request_handlers()
            user_id = qs.get('user_id', [None])[0]
            limit = self._get_qs_int(qs, 'limit', 200)

            if not user_id:
                auth_header = self.headers.get('Authorization', '')
                user_id = self._get_optional_user_id_from_auth(auth_header)

            if not user_id:
                return self._send_error(400, 'Missing user_id')

            result = handlers.handle_classify_unclassified(user_id=user_id, limit=limit)
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_gmail_message_get(self, parsed_path: str):
            """Handle /api/gmail/message/<id> GET endpoint."""
            message_id = parsed_path.split('/api/gmail/message/')[-1]
            auth_header = self.headers.get('Authorization', '')
            print(f"[RAG] /api/gmail/message/{message_id} - Auth header: {auth_header[:50] if auth_header else 'None'}...")
            user_id = self._get_optional_user_id_from_auth(auth_header)
            print(f"[RAG] Extracted user_id from token: {user_id}")
            print(f"[RAG] Final user_id for message body: {user_id}")

            handlers = self.get_request_handlers()
            result = handlers.handle_get_message_body(message_id, user_id)
            return self.json(result)

        def _handle_email_attachment_get(self, parsed_path: str):
            """Handle /api/email-attachment/<id> GET endpoint."""
            attachment_id = parsed_path.split('/api/email-attachment/')[-1].split('/')[0]
            auth_header = self.headers.get('Authorization', '')
            user_id = self._get_optional_user_id_from_auth(auth_header)

            handlers = self.get_request_handlers()
            status_code, headers, file_content = handlers.handle_email_attachment_download(attachment_id, user_id)

            self.send_response(status_code)
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
            self.end_headers()
            self.wfile.write(file_content)
            return

        def _handle_opportunities_search_get(self, qs, handlers):
            """Handle /api/opportunities/search GET endpoint."""
            source_reference_id = qs.get('source_reference_id', [None])[0]
            name = qs.get('name', [None])[0]

            user_id = self._require_auth_user_id()
            if user_id is None:
                return

            result = handlers.handle_search_opportunities(
                user_id=user_id,
                source_reference_id=source_reference_id,
                name=name,
            )
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_opportunity_actions_list_get(self, list_actions_match, handlers):
            """Handle /api/opportunities/<id>/actions GET endpoint."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return
            opportunity_id = list_actions_match.group(1)
            result = handlers.handle_list_actions(opportunity_id, user_id)
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_action_get(self, get_action_match, handlers):
            """Handle /api/actions/<id> GET endpoint."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return
            action_id = get_action_match.group(1)
            result = handlers.handle_get_action(action_id, user_id)
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_action_logs_get(self, get_action_logs_match, qs, handlers):
            """Handle /api/actions/<id>/logs GET endpoint."""
            user_id = self._require_auth_user_id()
            if user_id is None:
                return
            action_id = get_action_logs_match.group(1)
            limit = self._get_qs_int(qs, 'limit', 50)
            result = handlers.handle_get_action_logs(action_id, limit, user_id)
            status = 200 if result.get('status') == 'ok' else 400
            return self.json(result, status)

        def _handle_quotes_download_get(self, parsed_path: str, qs, handlers):
            """Handle /api/quotes/download/<filename> GET endpoint."""
            filename = parsed_path.split('/api/quotes/download/')[-1]
            return self._handle_quote_download(filename, handlers, qs)

        def _handle_documents_download_get(self, parsed_path: str, qs, handlers):
            """Handle /api/documents/download/<filename> GET endpoint."""
            filename = parsed_path.split('/api/documents/download/')[-1]
            filename = urllib.parse.unquote(filename)
            return self._handle_document_download(filename, handlers, qs)

        def _handle_csv_get(self, parsed_path: str, qs):
            """Handle /api/csv* GET endpoints."""
            handlers = self.get_request_handlers()

            if parsed_path == '/api/csv/files':
                return self._handle_csv_files_get(qs, handlers)
            if parsed_path == '/api/csv/preview':
                return self._handle_csv_preview_get(qs, handlers)
            if parsed_path == '/api/csv/raw':
                return self._handle_raw_stream(qs, handlers)
            if parsed_path == '/api/csv/source':
                return self._handle_source_stream(qs, handlers)
            if parsed_path == '/api/csv/download':
                return self._handle_csv_download(qs, handlers)
            if parsed_path == '/api/csv/sources':
                return self._handle_csv_sources_get(handlers)
            if parsed_path == '/api/csv/query':
                return self._handle_csv_query_get(qs, handlers)
            if parsed_path.startswith('/api/csv/search'):
                return self._handle_csv_search_get(qs, handlers)

            return None

        def _handle_csv_files_get(self, qs, handlers):
            """Handle /api/csv/files GET endpoint."""
            return self.json(handlers.handle_list_files(qs))

        def _handle_csv_preview_get(self, qs, handlers):
            """Handle /api/csv/preview GET endpoint."""
            return self.json(handlers.handle_preview(qs))

        def _handle_csv_sources_get(self, handlers):
            """Handle /api/csv/sources GET endpoint."""
            return self.json(handlers.handle_sources())

        def _handle_csv_query_get(self, qs, handlers):
            """Handle /api/csv/query GET endpoint."""
            return self.json(handlers.handle_query(qs))

        def _handle_csv_search_get(self, qs, handlers):
            """Handle /api/csv/search* GET endpoints."""
            return self.json(handlers.handle_search(qs, self.get_embedding_generator()))

        def _handle_quotes_list_get(self, handlers):
            """Handle /api/quotes/list GET endpoint."""
            return self.json(handlers.handle_list_quotes())

        def _get_qs_int(self, qs, key: str, default: int) -> int:
            """Read integer query-string parameter with fallback."""
            try:
                return int(qs.get(key, [default])[0])
            except Exception:
                return default

        def _get_qs_value(self, qs, key: str, default=None):
            """Read first query-string value with fallback."""
            return qs.get(key, [default])[0]

        def _get_payload_int(self, payload: Dict, key: str, default: int) -> int:
            """Read integer payload value with fallback."""
            try:
                return int(payload.get(key) or default)
            except Exception:
                return default

        def _get_optional_user_id_from_auth(self, auth_header: str):
            """Extract user id from auth header without enforcing auth."""
            if not auth_header:
                return None
            user_data = self._require_auth(auth_header=auth_header, required=False)
            return user_data.get('id') if user_data else None

        def _require_auth_user_id(self):
            """Require authenticated user and return its id."""
            user_data = self._require_auth()
            if user_data is None:
                return None
            return user_data.get('id') if user_data else None

        def _get_qs_bool(self, qs, key: str, default: bool = False) -> bool:
            """Read boolean query-string parameter with fallback."""
            raw_value = qs.get(key, [None])[0]
            if raw_value is None:
                return default
            return str(raw_value).strip().lower() in ('1', 'true', 'yes', 'on')

        def _handle_prompt_get(self, parsed_path: str):
            """Handle GET requests for prompt markdown content."""
            relative_path = parsed_path[len('/api/prompt/'):].strip('/')
            handlers = self.get_request_handlers()
            base_dir = Path(__file__).resolve().parents[1] / 'prompt'
            try:
                content = handlers.handle_get_prompt_content(
                    relative_path=relative_path,
                    prompt_base_dir=base_dir,
                )
            except ValueError as e:
                return self._send_error(400, str(e))
            except FileNotFoundError as e:
                return self._send_error(404, str(e))
            except Exception as e:
                return self._send_error(500, f"Error reading prompt: {e}")

            return self._send_text_response(200, 'text/plain; charset=utf-8', content.encode('utf-8'))

        def authorize(self) -> Dict:
            user_data = self._require_auth()
            if user_data is None:
                raise Exception({"Unauthorized"}, 401)
            return user_data

        def _require_auth(self, auth_header: str = None, required: bool = True) -> Dict:
            auth_header = auth_header if auth_header is not None else self.headers.get('Authorization', '')
            auth_handler = self.get_auth_handler()
            is_valid, user_data = auth_handler.verify_token(auth_header)
            if not is_valid:
                if required:
                    self.json({"error_code": "UNAUTHORIZED", "message": "Unauthorized"}, 401)
                return None
            return user_data

        def _read_body(self) -> bytes:
            content_length = int(self.headers.get('Content-Length', 0))
            return self.rfile.read(content_length)

        def _read_json(self, default=None):
            body = self._read_body()
            try:
                return json.loads(body.decode('utf-8') or '{}')
            except Exception:
                return {} if default is None else default

        def _read_json_or_error(self, error_payload=None, status_code=400):
            body = self._read_body()
            try:
                return json.loads(body.decode('utf-8') or '{}')
            except Exception:
                self.json(error_payload or {"status": "error", "message": "Invalid JSON"}, status_code)
                return None

        def _resolve_fs_path(self, raw_path: str):
            if not raw_path:
                self._send_error(400, 'Missing path')
                return None

            base_dir = Path(__file__).resolve().parents[3]
            input_path = Path(raw_path)

            if raw_path.startswith('~'):
                raw_path = raw_path[1:].lstrip('/')
                input_path = Path(raw_path)

            if input_path.is_absolute():
                try:
                    input_path = input_path.relative_to(base_dir)
                except Exception:
                    self._send_error(400, 'Invalid path')
                    return None

            target_path = (base_dir / input_path).resolve()

            if base_dir not in target_path.parents and target_path != base_dir:
                self._send_error(400, 'Invalid path')
                return None

            return target_path
        
        def _handle_raw_stream(self, qs, handlers):
            """Stream raw CSV file."""
            try:
                content = handlers.handle_raw(qs)
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                return self._send_error(500, f"Error streaming CSV: {e}")

        def _handle_csv_download(self, qs, handlers):
            """Download CSV file with proper filename."""
            try:
                source = (qs.get('source') or [None])[0]
                sheet = (qs.get('file') or [None])[0]
                
                if not source or not sheet:
                    return self._send_error(400, "Missing 'source' or 'file' parameter")
                
                # Get file path from file handler
                file_handler = handlers.file_handler
                csv_path = file_handler.safe_file_from_query(source, sheet)
                filename = sheet  # Use sheet name as filename
                file_size = csv_path.stat().st_size
                
                # Send response headers
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(file_size))
                self.end_headers()
                
                # Stream file in chunks to avoid memory issues
                with open(csv_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        
            except Exception as e:
                return self._send_error(500, f"Error downloading CSV: {e}")

        def _handle_source_stream(self, qs, handlers):
            """Stream original Excel source file."""
            try:
                source = (qs.get('source') or [None])[0]
                if not source:
                    return self._send_error(400, "Missing 'source' parameter")
                content = handlers.handle_source_raw(qs)
                ext = source.lower().split('.')[-1] if '.' in source else ''
                content_type_map = {
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'xls': 'application/vnd.ms-excel',
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Disposition', f'attachment; filename="{source}"')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                return self._send_error(500, f"Error streaming source: {e}")

        def _handle_quote_download(self, filename, handlers, qs=None):
            """Stream PDF quote file."""
            try:
                qs = qs or {}
                is_inline = qs.get('inline', ['0'])[0] == '1'
                content = handlers.handle_get_quote_file(filename)
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                disposition = 'inline' if is_inline else 'attachment'
                self.send_header('Content-Disposition', f'{disposition}; filename="{filename}"')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self._cors_header_sent = True
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                return self._send_error(404, "Quote file not found")
            except Exception as e:
                return self._send_error(500, f"Error streaming PDF: {e}")

        def _handle_document_download(self, filename, handlers, qs=None):
            """Stream document file (PDF, DOCX, etc.)."""
            try:
                qs = qs or {}
                is_inline = qs.get('inline', ['0'])[0] == '1'
                content = handlers.handle_get_document_file(filename)
                
                # Determine content type based on file extension
                ext = filename.lower().split('.')[-1] if '.' in filename else ''
                content_type_map = {
                    'pdf': 'application/pdf',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'doc': 'application/msword',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'xls': 'application/vnd.ms-excel',
                    'txt': 'text/plain; charset=utf-8',
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                disposition = 'inline' if is_inline else 'attachment'
                self.send_header('Content-Disposition', f'{disposition}; filename="{filename}"')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:5173')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self._cors_header_sent = True
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                return self._send_error(404, "Document file not found")
            except Exception as e:
                return self._send_error(500, f"Error streaming document: {e}")

        def json(self, payload, status_code=200):
            """Send JSON response."""
            try:
                data = json.dumps(payload).encode('utf-8')
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                # Client disconnected before receiving the response.
                return
            except Exception as e:
                try:
                    self._send_error(500, f"Error serializing JSON: {e}")
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    return

        def _send_error(self, code: int, message: str):
            """Send error response."""
            try:
                payload = json.dumps({"error": message}).encode('utf-8')
                self.send_response(code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

        def _send_text_response(self, code: int, content_type: str, body: bytes = None):
            """Send plain text/binary response payload."""
            try:
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                if body is not None:
                    self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if body is not None:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

        def _send_redirect(self, location: str, code: int = 302):
            """Send HTTP redirect response."""
            try:
                self.send_response(code)
                self.send_header('Location', location)
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return
    
    return Rag

class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    
    def server_bind(self):
        """Override to ensure SO_REUSEADDR is set before binding.
        
        SO_REUSEADDR allows rapid server restarts without waiting for TIME_WAIT.
        We do NOT use SO_REUSEPORT to prevent multiple servers on the same port.
        """
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()


def test_llm_connection():
    """Test LLM connectivity at startup.
    
    Attempts to connect to the configured LLM endpoint and verify the API is reachable.
    Logs status but does not block startup if LLM is unavailable.
    """
    def format_llm_error(error: Exception) -> str:
        parts = [f"{error.__class__.__name__}: {error}"]
        status_code = getattr(error, "status_code", None)
        if status_code is not None:
            parts.append(f"status={status_code}")

        response = getattr(error, "response", None)
        if response is not None:
            response_text = getattr(response, "text", None)
            if response_text:
                parts.append(f"response={response_text}")

        body = getattr(error, "body", None)
        if body:
            parts.append(f"body={body}")

        return " | ".join(parts)

    try:
        print("[LLM] Testing connection to LLM service...")
        factory = LLMClientFactory()
        client = factory.create_client(timeout=5)

        # A lightweight models list call verifies transport and auth without forcing
        # a full generation request, which can time out while the model is loading.
        response = client.client.models.list()
        models = []
        if hasattr(response, "data") and response.data:
            models = [getattr(item, "id", None) for item in response.data if getattr(item, "id", None)]

        requested_model = factory.get_settings().model
        if models and requested_model not in models:
            print(f"⚠️  [LLM] API reachable, but model '{requested_model}' is not in the local model list")
        else:
            print("✅ [LLM] Connection successful")
        return True
    except Exception as e:
        print(f"⚠️  [LLM] Connection failed: {format_llm_error(e)}")
        print(f"     LLM may be unavailable or misconfigured")
        print(f"     Make sure your LLM service is running at {os.environ.get('LLM_URL', 'http://127.0.0.1:1234')}")
        return False


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
