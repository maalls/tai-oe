"""Email-related request handlers for Gmail operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict

from src.infrastructure.factory import ServiceFactory
from src.infrastructure.clients.supabase import get_supabase_service
from src.service.email.auth_status_service import AuthStatusService
from src.service.email.quote_send_service import QuoteSendService
from src.lib.storage_paths import get_storage_dir, get_storage_path
from src.config import EMAIL_FETCH_MAX_RESULTS


def _get_legacy_repo():
    """Create legacy email repository lazily to avoid import-time side effects."""
    from src.repository.email_repository import EmailRepository

    return EmailRepository()


class EmailHandlers:
    """Handle email-related API requests.
    
    This class acts as a controller/handler layer that delegates
    business logic to the EmailRepository.
    """
    
    def __init__(self, service_factory: ServiceFactory = None):
        """Initialize email handlers."""
        self._repository = None
        self._quote_send_service = None
        self._auth_status_service = None
        self.service_factory = service_factory or ServiceFactory()

    @property
    def repository(self):
        if self._repository is None:
            self._repository = _get_legacy_repo()
        return self._repository

    @property
    def quote_send_service(self) -> QuoteSendService:
        if getattr(self, "_quote_send_service", None) is None:
            self._quote_send_service = QuoteSendService(
                send_email=self.repository.send_email,
                storage_path_resolver=self._get_storage_path,
                path_cls=Path,
                supabase_factory=get_supabase_service,
                now_provider=datetime.now,
            )
        return self._quote_send_service

    @property
    def auth_status_service(self) -> AuthStatusService:
        if getattr(self, "_auth_status_service", None) is None:
            self._auth_status_service = AuthStatusService(repository=self.repository)
        return self._auth_status_service
    
    def handle_gmail_authorize(self, redirect_url: str = None) -> Dict:
        """Trigger Gmail OAuth2 authorization flow.
        
        Parameters
        ----------
        redirect_url : str, optional
            URL to redirect to after successful authorization
        
        Returns
        -------
        Dict
            Response with status and message
        """
        return self.repository.authorize_gmail(redirect_url)

    def get_gmail_status(self, user_id: str = None) -> Dict:
        """Get the current status of Gmail."""
        return self.repository.get_gmail_status(user_id=user_id)

    def revoke_gmail(self, user_id: str = None) -> Dict:
        """Revoke Gmail authorization."""
        return self.repository.revoke_gmail(user_id=user_id)

    def get_gmail_profile(self, user_id: str = None) -> Dict:
        """Get Gmail profile and permissions."""
        return self.repository.get_gmail_profile(user_id=user_id)

    def get_imap_status(self, user_id: str) -> Dict:
        """Get IMAP configuration status."""
        return self.repository.get_imap_status(user_id)

    def get_imap_config(self, user_id: str) -> Dict:
        """Get IMAP configuration without secret value."""
        return self.repository.get_imap_config(user_id)

    def save_imap_config(self, user_id: str, payload: Dict) -> Dict:
        """Persist IMAP configuration for a user."""
        return self.repository.save_imap_config(user_id, payload)

    def clear_imap_config(self, user_id: str) -> Dict:
        """Remove IMAP configuration for a user."""
        return self.repository.clear_imap_config(user_id)

    def test_imap_connection(self, user_id: str) -> Dict:
        """Test IMAP connectivity for a user."""
        return self.repository.test_imap_connection(user_id)

    def get_gmail_oauth_url(self, redirect_url: str = None, user_id: str = None) -> Dict:
        """Start Gmail OAuth web flow."""
        return self.repository.get_gmail_oauth_url(redirect_url, user_id=user_id)

    def handle_gmail_oauth_callback(self, code: str, state: str = None) -> Dict:
        """Handle Gmail OAuth callback."""
        return self.repository.handle_gmail_oauth_callback(code, state)
    
    def handle_gmail_list_messages(
        self,
        max_results: int = 20,
        user_id: str = None,
        save_to_db: bool = True,
        force: bool = False
    ) -> Dict:
        """List messages from Gmail inbox.
        Uses cached results from database if fetched within last 30 seconds.
        
        Parameters
        ----------
        max_results : int
            Maximum number of messages to return
        user_id : str, optional
            Supabase user ID for saving emails to database
        save_to_db : bool
            Whether to save emails to Supabase database
        force : bool
            Force fetch from Gmail API, bypassing cache
        
        Returns
        -------
        Dict
            Response with list of messages
        """
        print(f"[EmailHandlers] Listing Gmail messages for user {user_id}, max_results={max_results}, save_to_db={save_to_db}, force={force}")
        return self.repository.fetch_emails(user_id, max_results=max_results, force=force)

    def handle_classify_unclassified(
        self,
        user_id: str,
        limit: int = 200,
    ) -> Dict:
        """Classify unclassified emails using the new workflow (fail-fast)."""
        try:
            workflow = self.service_factory.create_email_workflow_service()
            return workflow.classify_unclassified(user_id=user_id, limit=limit)
        except Exception as exc:
            print(f"[EmailHandlers] New workflow failed (fail-fast mode): {exc}")
            return {
                "status": "error",
                "workflow": "new",
                "message": f"New workflow failed: {exc}",
            }
    
    def handle_send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str = None,
        cc: str = None
    ) -> Dict:
        """Send an email with optional attachment.
        
        Parameters
        ----------
        to : str
            Recipient email address
        subject : str
            Email subject
        body : str
            Email body
        attachment_path : str, optional
            Path to attachment file
        
        Returns
        -------
        Dict
            Response with status and message
        """
        return self.repository.send_email(to, subject, body, attachment_path, cc=cc)

    def handle_send_email_with_attachments(
        self,
        to: list,
        cc: list,
        bcc: list = None,
        subject: str = '',
        body: str = '',
        attachment_paths: list = None,
        user_id: str = None,
    ) -> Dict:
        """Send an email with optional attachments to multiple recipients.

        Parameters
        ----------
        to : list
            List of recipient email addresses
        cc : list
            List of CC email addresses
        subject : str
            Email subject
        body : str
            Email body
        attachment_paths : list, optional
            List of attachment file paths (uses first if provided)

        Returns
        -------
        Dict
            Response with status and message
        """
        to_emails = ", ".join([e for e in (to or []) if e])
        cc_emails = ", ".join([e for e in (cc or []) if e]) if cc else None
        bcc_emails = ", ".join([e for e in (bcc or []) if e]) if bcc else None
        attachment_path = None
        if attachment_paths:
            attachment_path = attachment_paths[0]

        return self.repository.send_email(
            to=to_emails,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            cc=cc_emails,
            bcc=bcc_emails,
            user_id=user_id,
        )

    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        return self.quote_send_service.handle_quote_send(body=body, content_type=content_type)

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        return get_storage_dir(source)

    @staticmethod
    def _get_storage_path(source: str, filename: str) -> Path:
        return get_storage_path(source, filename)

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        return self.quote_send_service.handle_send_quote_for_opportunity(
            opportunity_id=opportunity_id,
            payload=payload,
            user_id=user_id,
        )
    
    def handle_get_message_body(self, uuid: str, user_id: str = None) -> Dict:
        """Get the full content of a message.
        
        Parameters
        ----------
        uuid : str
            ID of the message to fetch
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with full message content
        """
        return self.repository.get_message_body(uuid, user_id)

    def handle_email_attachment_download(self, attachment_id: str, user_id: str = None):
        """Download an email attachment.
        
        Parameters
        ----------
        attachment_id : str
            ID of the attachment to download
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Tuple of (status_code, headers, file_content)
            For serving as file download
        """
        return self.repository.get_attachment_download(attachment_id, user_id)

    def handle_email_attachment_delete(self, attachment_id: str, user_id: str = None) -> Dict:
        """Delete an email attachment.

        Parameters
        ----------
        attachment_id : str
            ID of the attachment to delete
        user_id : str, optional
            User ID for authorization
        """
        return self.repository.delete_attachment(attachment_id, user_id)

    def handle_email_delete(self, email_id: str, user_id: str = None) -> Dict:
        """Delete an email and all related records.

        Parameters
        ----------
        email_id : str
            ID of the email to delete
        user_id : str, optional
            User ID for authorization
        """
        return self.repository.delete_email(email_id, user_id)

    def handle_email_resync(self, email_id: str, provider_message_id: str, user_id: str) -> Dict:
        """Resync an email from Gmail using the legacy repository path."""
        return self.repository.resync_email_from_gmail(email_id, provider_message_id, user_id)

    def handle_extract_contact_from_email(self, email_id: str = None, email_body: str = None, user_id: str = None) -> Dict:
        """Extract contact and account information from email body using LLM.

        Parameters
        ----------
        email_id : str, optional
            ID of the email
        email_body : str
            Email body content to extract from
        user_id : str, optional
            User ID for database operations

        Returns
        -------
        Dict
            Response with extracted contact and account information
        """
        return self.repository.extract_contact_from_email_body(email_id=email_id, email_body=email_body, user_id=user_id)

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        """Create an opportunity from an existing email using the current backend path."""
        return self.repository.create_opportunity_from_email(message_id, user_id)

    def handle_get_email_auth_status(self, email_id: str, user_id: str) -> Dict:
        """Get authentication status for an email."""
        return self.auth_status_service.get_email_auth_status(email_id=email_id, user_id=user_id)

    def handle_get_high_risk_senders(self, user_id: str) -> Dict:
        """Get list of high-risk senders (low trust score)."""
        return self.auth_status_service.get_high_risk_senders(user_id=user_id)

    def handle_get_verified_senders(self, user_id: str) -> Dict:
        """Get list of verified senders (SPF+DKIM+DMARC all pass)."""
        return self.auth_status_service.get_verified_senders(user_id=user_id)


def handle_emails_classify_post(handler, parsed_path):
    """Handle /api/emails/classify/{email_uuid} POST endpoint."""
    email_uuid = parsed_path.split('/')[-1]

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id')
    print(f"[RAG] Classify request for email {email_uuid} by user {user_id}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_classify_email(email_uuid=email_uuid, user_id=user_id, force=True)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_extract_contact_post(handler):
    """Handle /api/email/extract-contact POST endpoint."""
    payload = handler._read_json(default={})

    email_id = payload.get('email_id')
    email_body = payload.get('email_body')

    if not email_body:
        return handler.json({"error": "Missing email_body parameter"}, 400)

    auth_header = handler.headers.get('Authorization', '')
    user_data = handler._require_auth(auth_header=auth_header, required=False)
    user_id = user_data.get('id') if user_data else None
    print(f"[RAG] Extract contact - Auth valid: {bool(user_data)}, user_id: {user_id}, auth_header: {auth_header[:50]}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_extract_contact_from_email(email_id=email_id, email_body=email_body, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_auth_status_post(handler, parsed_path):
    """Handle /api/email/auth/{email_id} POST endpoint."""
    email_id = parsed_path.split('/api/email/auth/')[-1]

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_email_auth_status(email_id=email_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_resync_post(handler, parsed_path):
    """Handle /api/email/{email_id}/resync POST endpoint."""
    path_parts = parsed_path.split('/')
    email_id = path_parts[-2] if len(path_parts) >= 4 else None

    if not email_id:
        return handler.json({"error": "Missing email_id"}, 400)

    payload = handler._read_json(default={})
    provider_message_id = payload.get('provider_message_id')
    if not provider_message_id:
        return handler.json({"error": "Missing provider_message_id"}, 400)

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_resync(email_id=email_id, provider_message_id=provider_message_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_senders_high_risk_post(handler):
    """Handle /api/email/senders/high-risk POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_high_risk_senders(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_senders_verified_post(handler):
    """Handle /api/email/senders/verified POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_verified_senders(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_imap_config_post(handler):
    """Handle /api/imap/config POST endpoint."""
    payload = handler._read_json(default={})

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_config_save(user_id=user_id, payload=payload)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_imap_test_post(handler):
    """Handle /api/imap/test POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_test(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_imap_config_delete(handler):
    """Handle DELETE /api/imap/config."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_config_delete(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_delete(handler, email_delete_match):
    """Handle DELETE /api/email/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    email_id = email_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_delete(email_id=email_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_attachment_delete(handler, attachment_delete_match):
    """Handle DELETE /api/email-attachment/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    attachment_id = attachment_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_attachment_delete(attachment_id=attachment_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_gmail_status_get(handler, qs):
    """Handle /api/gmail/status GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_status(user_id=user_id)
    return handler.json(result)


def handle_gmail_authorize_get(handler, qs):
    """Handle /api/gmail/authorize GET endpoint."""
    request_handlers = handler.get_request_handlers()
    redirect_url = handler._get_qs_value(qs, 'redirect_url')
    result = request_handlers.handle_gmail_authorize(redirect_url)
    return handler.json(result)


def handle_gmail_oauth_start_get(handler, qs):
    """Handle /api/gmail/oauth/start GET endpoint."""
    request_handlers = handler.get_request_handlers()
    redirect_url = handler._get_qs_value(qs, 'redirect_url')
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_oauth_start(redirect_url, user_id=user_id)
    return handler.json(result)


def handle_gmail_revoke_get(handler, qs):
    """Handle /api/gmail/revoke GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_revoke(user_id=user_id)
    return handler.json(result)


def handle_gmail_profile_get(handler, qs):
    """Handle /api/gmail/profile GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_profile(user_id=user_id)
    return handler.json(result)


def handle_imap_status_get(handler):
    """Handle /api/imap/status GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_status(user_id=user_id)
    return handler.json(result)


def handle_imap_config_get(handler):
    """Handle /api/imap/config GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_config(user_id=user_id)
    return handler.json(result)


def handle_gmail_messages_get(handler, qs):
    """Handle /api/gmail/messages GET endpoint."""
    request_handlers = handler.get_request_handlers()
    max_results = handler._get_qs_int(qs, 'max_results', EMAIL_FETCH_MAX_RESULTS)
    user_id = qs.get('user_id', [None])[0]
    force = handler._get_qs_bool(qs, 'force', False)

    print(f"[RAG] /api/gmail/messages - user_id from query: {user_id}, force: {force}")

    if not user_id:
        auth_header = handler.headers.get('Authorization', '')
        print(f"[RAG] Auth header: {auth_header[:50] if auth_header else 'None'}...")
        user_id = handler._get_optional_user_id_from_auth(auth_header)
        print(f"[RAG] Extracted user_id from token: {user_id}")

    print(f"[RAG] Final user_id: {user_id}")
    if not user_id:
        return handler._send_error(400, 'Missing user_id')

    result = request_handlers.handle_gmail_list_messages(
        max_results=max_results,
        user_id=user_id,
        save_to_db=True,
        force=force,
    )
    return handler.json(result)


def handle_gmail_classify_unclassified_get(handler, qs):
    """Handle /api/gmail/classify-unclassified GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = qs.get('user_id', [None])[0]
    limit = handler._get_qs_int(qs, 'limit', 200)

    if not user_id:
        auth_header = handler.headers.get('Authorization', '')
        user_id = handler._get_optional_user_id_from_auth(auth_header)

    if not user_id:
        return handler._send_error(400, 'Missing user_id')

    result = request_handlers.handle_classify_unclassified(user_id=user_id, limit=limit)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_gmail_message_get(handler, parsed_path: str):
    """Handle /api/gmail/message/<id> GET endpoint."""
    message_id = parsed_path.split('/api/gmail/message/')[-1]
    auth_header = handler.headers.get('Authorization', '')
    print(f"[RAG] /api/gmail/message/{message_id} - Auth header: {auth_header[:50] if auth_header else 'None'}...")
    user_id = handler._get_optional_user_id_from_auth(auth_header)
    print(f"[RAG] Extracted user_id from token: {user_id}")
    print(f"[RAG] Final user_id for message body: {user_id}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_message_body(message_id, user_id)
    return handler.json(result)


def handle_email_attachment_get(handler, parsed_path: str):
    """Handle /api/email-attachment/<id> GET endpoint."""
    attachment_id = parsed_path.split('/api/email-attachment/')[-1].split('/')[0]
    auth_header = handler.headers.get('Authorization', '')
    user_id = handler._get_optional_user_id_from_auth(auth_header)

    request_handlers = handler.get_request_handlers()
    status_code, headers, file_content = request_handlers.handle_email_attachment_download(attachment_id, user_id)

    handler.send_response(status_code)
    for header_name, header_value in headers.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()
    handler.wfile.write(file_content)
    return None


def handle_google_oauth_callback_get(handler, qs):
    """Handle Google OAuth callback route."""
    request_handlers = handler.get_request_handlers()
    code = qs.get('code', [None])[0]
    state = qs.get('state', [None])[0]
    if not code:
        return handler._send_error(400, 'Missing code parameter')

    result = request_handlers.handle_gmail_oauth_callback(code, state)
    if result.get('status') == 'ok':
        redirect_url = result.get('redirect_url') or 'http://localhost:5173/settings'
        return handler._send_redirect(redirect_url)

    return handler.json(result, 500)
