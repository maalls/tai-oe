"""
Gmail client for sending emails with attachments using Google OAuth2.
Extends the base GoogleAPIClient for authentication.
"""

import base64
import mimetypes
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from googleapiclient.errors import HttpError
from src.infrastructure.clients.oauth.google_client import GoogleAPIClient


class GmailClient(GoogleAPIClient):
    """Gmail client using OAuth2 credentials."""
    
    def __init__(
        self,
        credentials_path: str,
        token_path: str,
        redirect_url: str = None,
        token_bytes: bytes = None,
        token_saver=None,
    ):
        """
        Initialize Gmail client.
        
        Args:
            credentials_path: Path to OAuth2 credentials.json
            token_path: Path to token.pickle for storing auth token
            redirect_url: URL to redirect to after OAuth success
        """
        # Gmail send scope plus Drive/Sheets for shared credentials
        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
        ]
        
        super().__init__(
            credentials_path=credentials_path,
            token_path=token_path,
            scopes=scopes,
            redirect_url=redirect_url,
            token_bytes=token_bytes,
            token_saver=token_saver,
        )
    
    def get_service(self):
        """Get Gmail API service, creating if needed."""
        if self.service is None:
            try:
                self.authenticate('gmail', 'v1')
            except Exception as e:
                raise PermissionError(f"GMAIL_AUTH_ERROR: Failed to authenticate: {e}")
        
        return self.service
    
    def send_email_with_attachment(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        attachment_path: str = None,
        from_email: str = 'me',
        cc: str = None,
        bcc: str = None
    ) -> dict:
        """
        Send an email with optional PDF attachment.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachment_path: Path to the PDF file to attach (optional)
            from_email: Sender email (default 'me' = authenticated user)
        
        Returns:
            dict: Response from Gmail API with message id
        
        Raises:
            PermissionError: If authentication or permissions fail
            FileNotFoundError: If attachment file doesn't exist
            Exception: For other Gmail API errors
        """
        service = self.get_service()
        
        # Create message
        if attachment_path:
            attachment_path = Path(attachment_path)
            if not attachment_path.exists():
                raise FileNotFoundError(f"Attachment not found: {attachment_path}")
            message = MIMEMultipart()
        else:
            message = MIMEText(body, 'plain')
        
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Add body (only if multipart, otherwise set directly above)
        if attachment_path:
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachment
            content_type, _ = mimetypes.guess_type(str(attachment_path))
            if content_type is None:
                content_type = 'application/pdf'
            
            main_type, sub_type = content_type.split('/', 1)
            
            with open(attachment_path, 'rb') as f:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(f.read())
            
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment_path.name}"'
            )
            message.attach(attachment)
        
        # Encode and send
        try:
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': encoded_message}
            
            result = service.users().messages().send(
                userId=from_email, 
                body=send_message
            ).execute()
            
            return {
                'status': 'success',
                'message_id': result['id'],
                'to': to,
                'subject': subject
            }
        
        except HttpError as error:
            if error.resp.status == 403:
                raise PermissionError(
                    f"GMAIL_PERMISSION_ERROR: Insufficient permissions. "
                    f"Error: {error.error_details}"
                )
            else:
                raise Exception(f"Gmail API error: {error}")
        except Exception as e:
            raise Exception(f"Failed to send email: {e}")
    
    def list_messages(self, max_results: int = 20, user_id: str = 'me', query: str = None, page_token: str = None) -> dict:
        """
        List messages from Gmail inbox.
        
        Args:
            max_results: Maximum number of messages to return per page
            user_id: User's email (default 'me' = authenticated user)
            query: Gmail search query (e.g., 'after:2024/01/01' to get emails after a date)
            page_token: Token for pagination (to get next page of results)
        
        Returns:
            dict: List of messages with metadata, attachment info, and nextPageToken if more results exist
        
        Raises:
            PermissionError: If authentication or permissions fail
        """
        try:
            service = self.get_service()
            
            # List messages with optional query filter and pagination
            list_params = {
                'userId': user_id,
                'maxResults': max_results
            }
            if query:
                list_params['q'] = query
            if page_token:
                list_params['pageToken'] = page_token
            
            print(f"[GmailClient] Listing messages with params: {list_params}")
            results = service.users().messages().list(**list_params).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details for each
            detailed_messages = []

            def collect_attachments(part, found, seen_ids=None):
                """Recursively collect attachment metadata with attachmentId, deduplicating by ID."""
                if seen_ids is None:
                    seen_ids = set()
                
                if part.get('filename'):
                    body = part.get('body', {})
                    attachment_id = body.get('attachmentId')
                    # Only add attachment if we haven't seen this attachmentId before
                    if attachment_id and attachment_id not in seen_ids:
                        seen_ids.add(attachment_id)
                        found.append({
                            'filename': part.get('filename'),
                            'mimeType': part.get('mimeType'),
                            'attachmentId': attachment_id,
                            'size': body.get('size')
                        })
                for sub in part.get('parts', []) or []:
                    collect_attachments(sub, found, seen_ids)

            for msg in messages:
                msg_data = service.users().messages().get(
                    userId=user_id,
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extract headers with case-insensitive lookup
                # Handle both standard (From) and lowercase (from) header names
                headers_list = msg_data.get('payload', {}).get('headers', [])
                headers = {}
                headers_lower = {}
                for h in headers_list:
                    name = h.get('name', '')
                    value = h.get('value', '')
                    headers[name] = value
                    headers_lower[name.lower()] = value
                
                # Helper function for case-insensitive header lookup
                def get_header(name, default=''):
                    return headers.get(name) or headers_lower.get(name.lower(), default)
                
                # Collect attachments recursively
                attachments = []
                payload = msg_data.get('payload', {})
                collect_attachments(payload, attachments, set())
                
                has_attachments = len(attachments) > 0
                attachment_count = len(attachments)
                
                detailed_messages.append({
                    'id': msg_data['id'],
                    'threadId': msg_data.get('threadId'),
                    'from': get_header('From', ''),
                    'to': get_header('To', ''),
                    'cc': get_header('Cc', ''),
                    'subject': get_header('Subject', '(No Subject)'),
                    'date': get_header('Date', ''),
                    'snippet': msg_data.get('snippet', ''),
                    'labels': msg_data.get('labelIds', []),
                    'hasAttachments': has_attachments,
                    'attachmentCount': attachment_count,
                    'attachments': attachments
                })
            
            result_dict = {
                'status': 'success',
                'messages': detailed_messages,
                'total': len(detailed_messages)
            }
            
            # Include nextPageToken if there are more results
            if 'nextPageToken' in results:
                result_dict['nextPageToken'] = results['nextPageToken']
            
            return result_dict
        
        except HttpError as error:
            if error.resp.status == 403:
                raise PermissionError(
                    f"GMAIL_PERMISSION_ERROR: Insufficient permissions to read emails. "
                    f"Error: {error.error_details}"
                )
            else:
                raise Exception(f"Gmail API error: {error}")
        except Exception as e:
            raise Exception(f"Failed to list messages: {e}")    

    def download_attachment(self, message_id: str, attachment_id: str, dest_dir: Path, filename: str, user_id: str = 'me') -> Path:
        """Download an attachment and save it to dest_dir."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        service = self.get_service()

        attach = service.users().messages().attachments().get(
            userId=user_id,
            messageId=message_id,
            id=attachment_id
        ).execute()

        data = attach.get('data')
        if not data:
            raise ValueError("Attachment data is empty")

        content = base64.urlsafe_b64decode(data.encode('UTF-8'))
        file_path = dest_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    def get_message_body(self, message_id: str, user_id: str = 'me') -> dict:
        """
        Get the full body/content of a message.
        
        Args:
            message_id: ID of the message to fetch
            user_id: User's email (default 'me' = authenticated user)
        
        Returns:
            dict: Message with full content, headers, and metadata
        
        Raises:
            PermissionError: If authentication or permissions fail
        """
        try:
            service = self.get_service()
            
            # Fetch full message
            msg_data = service.users().messages().get(
                userId=user_id,
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
            
            # Extract body (both HTML and plain text)
            import base64
            
            def extract_body_parts(part):
                """Recursively extract text/plain and text/html from message parts."""
                html_body = None
                text_body = None
                
                if 'parts' in part:
                    # Multipart message - recursively process parts
                    for subpart in part['parts']:
                        sub_html, sub_text = extract_body_parts(subpart)
                        if sub_html and not html_body:
                            html_body = sub_html
                        if sub_text and not text_body:
                            text_body = sub_text
                else:
                    # Single part
                    mime_type = part.get('mimeType', '')
                    body_data = part.get('body', {}).get('data')
                    
                    if body_data:
                        try:
                            decoded = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            if mime_type == 'text/html':
                                html_body = decoded
                            elif mime_type == 'text/plain':
                                text_body = decoded
                        except Exception as e:
                            print(f"[GmailClient] Error decoding body part: {e}")
                
                return html_body, text_body
            
            payload = msg_data.get('payload', {})
            html_body, text_body = extract_body_parts(payload)
            
            # Prefer HTML over plain text
            body = html_body if html_body else text_body if text_body else ''
            
            return {
                'status': 'success',
                'id': msg_data['id'],
                'threadId': msg_data.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'cc': headers.get('Cc', ''),
                'subject': headers.get('Subject', '(No Subject)'),
                'date': headers.get('Date', ''),
                'body': body,
                'labels': msg_data.get('labelIds', [])
            }
        
        except HttpError as error:
            if error.resp.status == 403:
                raise PermissionError(
                    f"GMAIL_PERMISSION_ERROR: Insufficient permissions to read email. "
                    f"Error: {error.error_details}"
                )
            else:
                raise Exception(f"Gmail API error: {error}")
        except Exception as e:
            raise Exception(f"Failed to get message: {e}")