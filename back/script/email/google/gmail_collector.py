#!/usr/bin/env python3
"""
Gmail Unread Email Collector
Connects to Gmail API and fetches unread emails with their content.
"""

import argparse
import base64
import html
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from googleapiclient.errors import HttpError

from ...common.google_auth import GoogleAPIClient
from src.repository.classifier.classifier import EmailClassifier

class GmailCollector(GoogleAPIClient):
    """Collect and parse unread emails from Gmail."""

    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """Initialize Gmail collector.

        Parameters
        ----------
        credentials_path : Optional[str]
            Path to OAuth2 credentials JSON file from Google Cloud Console.
            If None, uses var/credentials.json relative to project root.
        token_path : Optional[str]
            Path to store/load authentication token for reuse.
            If None, uses var/token.pickle relative to project root.
        """
        super().__init__(credentials_path, token_path)

    def authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        super().authenticate("gmail", "v1")

    def     get_unread_emails(self, max_results: int = 10, query: str = "is:unread", attachments_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch unread emails.

        Parameters
        ----------
        max_results : int
            Maximum number of emails to fetch
        query : str
            Gmail search query (default: "is:unread")

        Returns
        -------
        List[Dict[str, Any]]
            List of email dictionaries with id, subject, from, date, body, snippet
        """
        if not self.service:
            self.authenticate()

        # Prepare attachments directory
        attach_dir = Path(attachments_dir or os.environ.get("ATTACHMENTS_DIR", "var/attachments"))
        attach_dir.mkdir(parents=True, exist_ok=True)

        emails = []

        try:
            # Get list of unread message IDs
            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()

            messages = results.get("messages", [])

            if not messages:
                print("No unread emails found.")
                return emails

            # Fetch full details for each message
            for msg in messages:
                msg_id = msg["id"]
                message = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()

                email_data = self._parse_email(message)
                # Download attachments and include in email data
                saved, cid_map = self._download_attachments(msg_id, message.get("payload", {}), attach_dir)
                if saved:
                    email_data["attachments"] = saved
                if cid_map:
                    email_data["cid_map"] = cid_map
                    # Replace cid: references in body with file URLs
                    email_data["body"] = self._replace_cid_urls(email_data["body"], cid_map)

                self.process(email_data)  # Optional processing hook
                emails.append(email_data)

        except HttpError as error:
            print(f"An error occurred: {error}")

        return emails
    
    def process(self, email: Dict[str, Any]) -> None:
        """Optional hook to process each email after fetching.

        Can be overridden in subclasses for custom processing.

        Parameters
        ----------
        email : Dict[str, Any]
            Parsed email dictionary
        """
        # Skip if already classified (from cache)
        if email.get("classification"):
            cached = email["classification"]
            category = cached.get("category")
            reason = cached.get("reason")
            new_category = cached.get("new_category")

            print(f"  📧 Classification (cached): {category}")
            if reason:
                print(f"     Reason: {reason}")
            if category == "Other" and new_category:
                print(f"     Suggested category: {new_category}")
            return

        # Get the email title and body and pass it to the classifier
        subject = email.get("subject", "")
        body = email.get("body", "")
        
        if subject and body:
            # Crop body to reasonable length for LLM (approx 2000 chars)
            max_body_length = 2000
            if len(body) > max_body_length:
                # Crop at word boundary
                cropped = body[:max_body_length]
                # Find last space to avoid cutting words
                last_space = cropped.rfind(" ")
                if last_space > max_body_length - 500:  # Only if space is reasonably close
                    body = body[:last_space] + "..."
                else:
                    body = cropped + "..."
            
            try:
                classifier = EmailClassifier()
                classification = classifier.classify(subject, body, email.get("from"))
                email["classification"] = classification
                category = classification.get("category")
                reason = classification.get("reason")
                new_category = classification.get("new_category")
                print(f"  📧 Classification (new): {category}")
                if reason:
                    print(f"     Reason: {reason}")
                if category == "Other" and new_category:
                    print(f"     Suggested category: {new_category}")
            except Exception as e:
                # Log error with email details for investigation
                print(f"  ⚠️  Skipped classification: {type(e).__name__}")
                print(f"      Subject: {subject[:80]}{'...' if len(subject) > 80 else ''}")
                print(f"      From: {email.get('from', 'Unknown')}")
                print(f"      Body length: {len(body)} chars")
        

    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message to extract relevant fields.

        Parameters
        ----------
        message : Dict[str, Any]
            Raw Gmail API message object

        Returns
        -------
        Dict[str, Any]
            Parsed email with id, subject, from, to, date, body, snippet
        """
        headers = message.get("payload", {}).get("headers", [])

        # Extract common headers
        subject = self._get_header(headers, "Subject")
        from_addr = self._get_header(headers, "From")
        to_addr = self._get_header(headers, "To")
        date = self._get_header(headers, "Date")

        # Extract body
        body = self._get_email_body(message.get("payload", {}))
        body = self._sanitize_body(body)  # Remove cid: image references

        return {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "subject": html.unescape(subject) if subject else None,
            "from": html.unescape(from_addr) if from_addr else None,
            "to": html.unescape(to_addr) if to_addr else None,
            "date": date,
            "snippet": html.unescape(message.get("snippet", "")),
            "body": html.unescape(body),
            "labels": message.get("labelIds", []),
        }

    def _get_header(self, headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value")
        return None

    def _sanitize_body(self, body: str) -> str:
        """Remove cid: (Content-ID) image references from email body.
        
        cid: URLs are inline attachments and cannot be displayed as regular URLs.
        This removes img tags with cid: src attributes.
        
        Parameters
        ----------
        body : str
            Email body (HTML or plain text)
        
        Returns
        -------
        str
            Sanitized body
        """
        import re
        # Remove img tags with cid: src
        body = re.sub(r'<img[^>]*src=["\']cid:[^"\'>]*["\'][^>]*>', '', body, flags=re.IGNORECASE)
        return body

    def _replace_cid_urls(self, body: str, cid_map: Dict[str, str]) -> str:
        """Replace cid: URLs in email body with actual file URLs.
        
        Parameters
        ----------
        body : str
            Email body (HTML)
        cid_map : Dict[str, str]
            Mapping of Content-ID to file path
        
        Returns
        -------
        str
            Body with cid: URLs replaced
        """
        import re
        for cid, filepath in cid_map.items():
            # Replace cid:XXX with file URL (relative path)
            pattern = f'cid:{re.escape(cid)}'
            replacement = f'file://{filepath}'  # or relative path
            body = body.replace(pattern, replacement)
        return body

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from message payload.

        Handles both plain text and multipart messages.
        """
        body = ""

        # Check if payload has parts (multipart)
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
                elif part.get("mimeType") == "text/html" and not body:
                    # Fallback to HTML if no plain text
                    data = part.get("body", {}).get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                elif "parts" in part:
                    # Recursive for nested parts
                    body = self._get_email_body(part)
                    if body:
                        break
        else:
            # Single part message
            data = payload.get("body", {}).get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        return body

    def _download_attachments(self, message_id: str, payload: Dict[str, Any], attach_dir: Path) -> List[str]:
        """Download attachments from the message payload to `attach_dir`.

        Returns a list of saved file paths.
        """
        saved_files: List[str] = []

        def walk_parts(parts: List[Dict[str, Any]]):
            for part in parts:
                filename = part.get("filename") or ""
                body_info = part.get("body", {})
                att_id = body_info.get("attachmentId")
                mime = part.get("mimeType") or "application/octet-stream"

                # Nested parts
                if "parts" in part:
                    walk_parts(part["parts"])

                # If there's an attachmentId or a filename present, attempt download
                if att_id or (filename and not body_info.get("data")):
                    try:
                        # Fetch attachment content via Gmail API
                        att = self.service.users().messages().attachments().get(
                            userId="me", messageId=message_id, id=att_id
                        ).execute()

                        data_b64 = att.get("data")
                        if not data_b64:
                            continue

                        content = base64.urlsafe_b64decode(data_b64)

                        # Determine filename
                        safe_name = self._safe_filename(filename) if filename else self._guess_filename(mime)
                        target = self._dedupe_path(attach_dir / safe_name)

                        with open(target, "wb") as f:
                            f.write(content)

                        saved_files.append(str(target))
                    except HttpError as e:
                        # Skip problematic attachment but continue others
                        print(f"Attachment download error for message {message_id}: {e}")

        if payload.get("parts"):
            walk_parts(payload["parts"])

        return saved_files

    def _safe_filename(self, name: str) -> str:
        """Sanitize filename to prevent path traversal and illegal chars."""
        name = name.strip().replace("\\", "_").replace("/", "_")
        # Avoid very long names
        return name[:255] or "attachment.bin"

    def _guess_filename(self, mime: str) -> str:
        """Guess a filename from MIME type when none provided."""
        ext = {
            "text/plain": ".txt",
            "text/html": ".html",
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
        }.get(mime, ".bin")
        return f"attachment{ext}"

    def _dedupe_path(self, path: Path) -> Path:
        """If path exists, add numeric suffix to avoid overwrite."""
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        i = 1
        while True:
            candidate = parent / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                return candidate
            i += 1

    def mark_as_read(self, message_id: str) -> None:
        """Mark an email as read."""
        if not self.service:
            self.authenticate()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            print(f"Marked message {message_id} as read")
        except HttpError as error:
            print(f"Error marking message as read: {error}")


def main():
    """Example usage: collect and display unread emails."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Collect unread emails from Gmail")
    parser.add_argument(
        "-c", "--cache",
        action="store_true",
        help="Use cached emails instead of fetching from Gmail API"
    )
    args = parser.parse_args()

    # Initialize collector
    # Default to var/credentials.json and var/token.pickle relative to project root
    default_credentials = Path(__file__).resolve().parents[3] / "var" / "credentials.json"
    default_token = Path(__file__).resolve().parents[3] / "var" / "token.pickle"
    default_output_file = default_credentials.parent / "unread_emails.json"
    output_file = os.environ.get("OUTPUT_FILE", str(default_output_file))

    # Check if cache flag is set and cache file exists
    emails = None
    collector = None
    if args.cache:
        if Path(output_file).exists():
            print(f"📦 Loading emails from cache: {output_file}")
            with open(output_file, "r", encoding="utf-8") as f:
                emails = json.load(f)
            print(f"✅ Loaded {len(emails)} emails from cache\n")
            # Create collector instance for processing
            collector = GmailCollector(
                credentials_path=os.environ.get("GMAIL_CREDENTIALS", default_credentials),
                token_path=os.environ.get("GMAIL_TOKEN", default_token),
            )
        else:
            print(f"⚠️  Cache file not found: {output_file}")
            print("Proceeding to fetch from Gmail API...\n")

    # Fetch from API if not using cache or cache file not found
    if emails is None:
        collector = GmailCollector(
            credentials_path=os.environ.get("GMAIL_CREDENTIALS", default_credentials),
            token_path=os.environ.get("GMAIL_TOKEN", default_token),
        )

        # Authenticate
        print("Authenticating with Gmail...")
        collector.authenticate()

        # Fetch unread emails
        max_emails = int(os.environ.get("MAX_EMAILS", "10"))
        print(f"\nFetching up to {max_emails} unread emails...\n")

        emails = collector.get_unread_emails(max_results=max_emails)

        classified_count = sum(1 for email in emails if email.get("classification"))

        print(f"  {classified_count}/{len(emails)} emails classified")

        # Save to JSON file
        # Looking at the dump shows some google preprocessed categories
        #  - labels: [CATEGORY_UPDATES, CATEGORY_PROMOTIONS, CATEGORY_PERSONAL, and CATEGORY_SOCIAL]
        # CATEGORY_UPDATES: Gmail applies this label automatically to emails that are service notifications, 
        # account alerts, order confirmations, billing statements, and similar 
        # transactional updates from companies and services. 
        # It's one of Gmail's smart categories to help organize inbox clutter alongside
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(emails, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved {len(emails)} emails to {output_file}\n")

    # Process emails with classifier (if not already done during fetch)
    if collector and args.cache:
        print("Classifying emails...\n")
        for email in emails:
            collector.process(email)

    # Display emails
    for i, email in enumerate(emails, 1):
        print(f"{'='*80}")
        print(f"Email {i}/{len(emails)}")
        print(f"{'='*80}")
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Snippet: {email['snippet']}")
        
        # Display classification if available
        classification = email.get("classification")
        if classification:
            category = classification.get("category")
            reason = classification.get("reason")
            new_category = classification.get("new_category")

            print(f"\n📧 Classification: {category}")
            if reason:
                print(f"   Reason: {reason}")
            if category == "Other" and new_category:
                print(f"   Suggested category: {new_category}")
        print()


if __name__ == "__main__":
    main()
