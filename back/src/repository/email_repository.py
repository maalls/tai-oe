"""Business logic for email operations."""

import email
import imaplib
from html.parser import HTMLParser
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import re
import pickle
import base64
import json
import os
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime
from email.header import decode_header
from cryptography.fernet import Fernet, InvalidToken

from src.service.classification.service import EmailClassifier
from src.infrastructure.clients.gmail_client import GmailClient
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_rfp_from_text
from src.lib.email.mime import parse_from_header
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import Flow


PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "yandex.com",
    "gmx.com",
    "live.com",
    "msn.com",
    "me.com",
    "mail.com",
}


def _normalize_iso_datetime(date_string: str) -> Optional[str]:
    """Normalize ISO datetime strings for datetime.fromisoformat."""
    if not date_string:
        return None
    iso_candidate = date_string.strip().replace("Z", "+00:00")
    frac_match = re.match(r"^(.*T[0-9:]+)\.([0-9]+)(.*)$", iso_candidate)
    if frac_match:
        frac = frac_match.group(2)[:6].ljust(6, "0")
        iso_candidate = f"{frac_match.group(1)}.{frac}{frac_match.group(3)}"
    return iso_candidate


def _dedupe_path(path: Path) -> Path:
    """If path exists, add numeric suffix to avoid overwriting duplicate filenames.
    
    This ensures that attachments with the same filename don't overwrite each other.
    For example: report.pdf -> report_1.pdf, report_2.pdf, etc.
    """
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


def _resolve_frontend_redirect_url(default_path: str = "/settings") -> str:
    """Resolve the frontend redirect URL from the public frontend base URL."""
    configured = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153").strip()
    parsed = urlparse(configured)

    if not parsed.scheme or not parsed.netloc:
        return f"http://localhost:7153{default_path}"

    path = parsed.path.rstrip("/")
    if path:
        return configured.rstrip("/")

    return f"{parsed.scheme}://{parsed.netloc}{default_path}"


class EmailDatabaseHandler:
    """Handle email storage in Supabase database."""

    def __init__(self):
        self.supabase = get_supabase_service()

    def _resolve_gmail_callback_url(self, redirect_url: Optional[str]) -> str:
        """Resolve OAuth callback URL from frontend redirect URL origin.

        This avoids hardcoded backend ports in local environments.
        """
        env_callback = os.getenv("GMAIL_OAUTH_CALLBACK_URL")
        if env_callback:
            return env_callback

        default_origin = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153")
        candidate = redirect_url or default_origin
        parsed = urlparse(candidate)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/api/gmail/oauth/callback"

        return "http://localhost:7153/api/gmail/oauth/callback"

    
    def _parse_email_date(self, date_string: str) -> Optional[str]:
        """Parse email date string to ISO format (UTC)."""
        if not date_string:
            raise ValueError("email_date is required but missing")

        try:
            dt = parsedate_to_datetime(date_string)
        except (TypeError, ValueError):
            iso_candidate = _normalize_iso_datetime(date_string)
            if not iso_candidate:
                raise ValueError(f"Unparseable email_date: '{date_string}'")
            dt = datetime.fromisoformat(iso_candidate)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()

    def store_email(
        self,
        user_id: str,
        provider: str,
        provider_message_id: str,
        subject: str,
        from_email: str,
        to_email: str,
        email_date: str,
        body_preview: str,
        body_full: Optional[str] = None,
        category: Optional[str] = None,
        classification_reason: Optional[str] = None,
        provider_thread_id: Optional[str] = None,
        provider_account_id: Optional[str] = None,
        provider_metadata: Optional[Dict] = None,
        from_name: Optional[str] = None,
        from_raw: Optional[str] = None,
        from_domain: Optional[str] = None,
        from_local: Optional[str] = None,
        from_is_valid: Optional[bool] = None,
        cc_email: Optional[str] = None,
        contact_id: Optional[str] = None,
        account_id: Optional[str] = None,
        spf_status: Optional[str] = None,
        dkim_status: Optional[str] = None,
        dmarc_status: Optional[str] = None,
        auth_score: Optional[int] = None,
        is_verified: Optional[bool] = None,
        auth_headers: Optional[Dict] = None,
    ) -> Dict:
        """Store an email in the database."""

        existing_classification = None
        try:
            existing = (
                self.supabase.table("email")
                .select("category, classification_reason, is_classified, classified_at, category_suggestion, important")
                .eq("user_id", user_id)
                .eq("provider", provider)
                .eq("provider_message_id", provider_message_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                existing_classification = existing.data[0]
        except Exception:
            pass

        email_data = {
            "user_id": user_id,
            "provider": provider,
            "provider_message_id": provider_message_id,
            "provider_thread_id": provider_thread_id,
            "provider_account_id": provider_account_id,
            "subject": subject,
            "from_email": from_email,
            "from_name": from_name,
            "from_raw": from_raw,
            "from_domain": from_domain,
            "from_local": from_local,
            "from_is_valid": from_is_valid,
            "to_email": to_email,
            "cc_email": cc_email,
            "contact_id": contact_id,
            "account_id": account_id,
            "email_date": self._parse_email_date(email_date),
            "body_preview": body_preview,
            "body_full": body_full,
            "category": category,
            "classification_reason": classification_reason,
            "is_classified": category is not None,
            "classified_at": datetime.utcnow().isoformat() if category else None,
            "provider_metadata": provider_metadata or {},
            "fetched_at": datetime.utcnow().isoformat(),
            "spf_status": spf_status or "NONE",
            "dkim_status": dkim_status or "NONE",
            "dmarc_status": dmarc_status or "NONE",
            "auth_score": auth_score or 0,
            "is_verified": is_verified or False,
            "auth_headers": auth_headers or {},
            "sender_verified_at": datetime.utcnow().isoformat() if is_verified else None,
        }

        if existing_classification and existing_classification.get("is_classified") and not category:
            email_data["category"] = existing_classification.get("category")
            email_data["classification_reason"] = existing_classification.get("classification_reason")
            email_data["is_classified"] = True
            email_data["classified_at"] = existing_classification.get("classified_at")
            email_data["category_suggestion"] = existing_classification.get("category_suggestion")
            email_data["important"] = existing_classification.get("important")

        payload = dict(email_data)

        def _existing_email_id() -> Optional[str]:
            try:
                existing = (
                    self.supabase.table("email")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("provider", provider)
                    .eq("provider_message_id", provider_message_id)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    return existing.data[0]["id"]
            except Exception:
                pass
            return None

        # Retry loop to tolerate schema drift (missing columns in PostgREST cache).
        for _ in range(10):
            try:
                response = self.supabase.table("email").upsert(
                    payload,
                    on_conflict="user_id,provider,provider_message_id"
                ).execute()

                if response.data:
                    return {
                        "success": True,
                        "email_id": response.data[0]["id"] if isinstance(response.data, list) else response.data["id"],
                    }

                existing_id = _existing_email_id()
                if existing_id:
                    return {"success": True, "email_id": existing_id, "skipped": True}
                return {"success": False, "error": "Failed to insert email"}
            except Exception as e:
                error_text = str(e)

                # No matching unique constraint for ON CONFLICT -> fallback to plain insert.
                if "no unique or exclusion constraint" in error_text.lower():
                    try:
                        ins_response = self.supabase.table("email").insert(payload).execute()
                        if ins_response.data:
                            return {
                                "success": True,
                                "email_id": ins_response.data[0]["id"] if isinstance(ins_response.data, list) else ins_response.data["id"],
                            }
                    except Exception:
                        existing_id = _existing_email_id()
                        if existing_id:
                            return {"success": True, "email_id": existing_id, "skipped": True}
                    return {"success": False, "error": error_text}

                # Missing column in schema cache: remove it and retry.
                missing_col_match = re.search(r"Could not find the '([^']+)' column", error_text)
                if missing_col_match:
                    missing_col = missing_col_match.group(1)
                    if missing_col in payload:
                        print(f"[EmailRepository] Email schema mismatch: removing missing column '{missing_col}' and retrying")
                        payload.pop(missing_col, None)
                        continue

                # Backward compatibility for old fallback behavior.
                if "contact_id" in error_text or "account_id" in error_text:
                    payload.pop("contact_id", None)
                    payload.pop("account_id", None)
                    continue

                existing_id = _existing_email_id()
                if existing_id:
                    return {"success": True, "email_id": existing_id, "skipped": True}
                return {"success": False, "error": error_text}

        existing_id = _existing_email_id()
        if existing_id:
            return {"success": True, "email_id": existing_id, "skipped": True}
        return {"success": False, "error": "Failed to insert email after schema fallback retries"}

    def add_labels(self, email_id: str, labels: List[Dict[str, str]]) -> Dict:
        """Add labels to an email."""

        label_data = [
            {
                "email_id": email_id,
                "provider_label_id": label.get("label_id", label.get("provider_label_id")),
                "label_name": label.get("label_name", label.get("name")),
            }
            for label in labels
        ]

        try:
            # Upsert to avoid duplicate constraint errors on (email_id, provider_label_id)
            response = (
                self.supabase.table("email_labels")
                .upsert(label_data, on_conflict="email_id,provider_label_id")
                .execute()
            )
            return {"success": True, "labels_added": len(response.data) if response.data else 0}
        except Exception as exc:  # pragma: no cover
            print(f"Error upserting labels: {exc}")
            return {"success": False, "error": str(exc)}

    def add_attachments(self, email_id: str, attachments: List[Dict[str, str]]) -> Dict:
        """Persist attachment metadata for an email."""
        attachment_data = []
        for attachment in attachments:
            provider_attachment_id = attachment.get("provider_attachment_id")
            if not provider_attachment_id:
                continue
            attachment_data.append(
                {
                    "email_id": email_id,
                    "provider_attachment_id": provider_attachment_id,
                    "filename": attachment.get("filename"),
                    "mime_type": attachment.get("mime_type"),
                    "size": attachment.get("size"),
                    "storage_path": attachment.get("storage_path"),
                }
            )

        if not attachment_data:
            return {"success": True, "attachments_added": 0}

        try:
            response = (
                self.supabase.table("email_attachment")
                .upsert(attachment_data, on_conflict="email_id,provider_attachment_id")
                .execute()
            )
            return {"success": True, "attachments_added": len(response.data) if response.data else 0}
        except Exception as exc:  # pragma: no cover
            print(f"Error upserting attachments: {exc}")
            return {"success": False, "error": str(exc)}

    def get_labels(self, email_id: str) -> List[Dict]:
        """Get all labels for an email."""
        response = (
            self.supabase.table("email_labels")
            .select("label_name, provider_label_id")
            .eq("email_id", email_id)
            .execute()
        )
        return response.data if response.data else []

    def get_email(self, email_id: str) -> Optional[Dict]:
        """Get a single email by ID for a user."""
        try:
            response = (
                self.supabase.table("email")
                .select("*")
                .eq("id", email_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Error getting email: {exc}")
            return None

    def get_emails_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get emails for a user."""
        response = (
            self.supabase.table("email")
            .select("*")
            .eq("user_id", user_id)
            .order("email_date", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    def get_emails_by_category(self, user_id: str, category: str, limit: int = 100) -> List[Dict]:
        """Get emails by category."""
        try:
            response = (
                self.supabase.table("email")
                .select("*")
                .eq("user_id", user_id)
                .eq("category", category)
                .order("email_date", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data if response.data else []
        except Exception as exc:  # pragma: no cover
            print(f"Error getting emails by category: {exc}")
            return []

    def get_unclassified_emails(self, user_id: str, limit: int = 200) -> List[Dict]:
        """Return emails missing classification for a user."""
        try:
            response = (
                self.supabase.table("email")
                .select("id, subject, from_email, body_full, body_preview")
                .eq("user_id", user_id)
                .is_("is_classified", False)
                .order("email_date", desc=True)
                .limit(limit)
                .execute()
            )
            data = response.data or []

            # Also capture null is_classified to backfill older rows
            if len(data) < limit:
                remaining = limit - len(data)
                null_response = (
                    self.supabase.table("email")
                    .select("id, subject, from_email, body_full, body_preview")
                    .eq("user_id", user_id)
                    .is_("is_classified", None)
                    .order("email_date", desc=True)
                    .limit(remaining)
                    .execute()
                )
                if null_response.data:
                    data.extend(null_response.data)

            return data
        except Exception as exc:  # pragma: no cover
            print(f"Error getting unclassified emails: {exc}")
            return []

    def get_latest_fetch_time(self, user_id: str, provider: str = "gmail") -> Optional[datetime]:
        """Get the timestamp of the last fetch from the provider."""
        response = (
            self.supabase.table("email_fetch_metadata")
            .select("last_fetch_at")
            .eq("user_id", user_id)
            .eq("provider", provider)
            .limit(1)
            .execute()
        )
        if response.data:
            fetch_at_str = response.data[0].get("last_fetch_at")
            if fetch_at_str:
                normalized = _normalize_iso_datetime(fetch_at_str)
                return datetime.fromisoformat(normalized) if normalized else None
        return None
    
    def get_last_fetched_email_id(self, user_id: str, provider: str = "gmail") -> Optional[str]:
        """Get the provider_message_id of the most recently fetched email."""
        response = (
            self.supabase.table("email")
            .select("provider_message_id")
            .eq("user_id", user_id)
            .eq("provider", provider)
            .order("email_date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0].get("provider_message_id")
        return None

    def update_email_classification(
        self,
        email_uuid: str,
        user_id: str,
        category: str,
        category_suggestion: str,
        classification_reason: str,
        is_classified: bool = True,
        important: bool = False,
        classified_at: str = None,
    ) -> bool:
        """Update email classification fields."""
        try:
            update_data = {
                "category": category,
                "category_suggestion": category_suggestion,
                "classification_reason": classification_reason,
                "is_classified": is_classified,
                "important": important,
                "classified_at": classified_at or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            response = (
                self.supabase.table("email")
                .update(update_data)
                .eq("id", email_uuid)
                .eq("user_id", user_id)
                .execute()
            )
            return bool(response.data)
        except Exception as exc:  # pragma: no cover
            print(f"Error updating email classification: {exc}")
            return False


class EmailRepository:
    """Repository for email business logic and data operations."""

    IMAP_PASSWORD_PREFIX = "fernet:"
    
    def __init__(self):
        """Initialize email repository."""
        self.db_handler = EmailDatabaseHandler()

    def _resolve_gmail_callback_url(self, redirect_url: Optional[str]) -> str:
        """Resolve OAuth callback URL from frontend redirect URL origin."""
        env_callback = os.getenv("GMAIL_OAUTH_CALLBACK_URL")
        if env_callback:
            return env_callback

        default_origin = os.getenv("FRONTEND_BASE_URL", "http://localhost:7153")
        candidate = redirect_url or default_origin
        parsed = urlparse(candidate)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/api/gmail/oauth/callback"

        return "http://localhost:7153/api/gmail/oauth/callback"

    @staticmethod
    def _get_secret_fernet() -> Fernet:
        raw_key = os.getenv("APP_SECRETS_ENCRYPTION_KEY")
        if not raw_key:
            raise RuntimeError("APP_SECRETS_ENCRYPTION_KEY is not set")
        try:
            return Fernet(raw_key.encode("utf-8"))
        except Exception as exc:
            raise RuntimeError("APP_SECRETS_ENCRYPTION_KEY is invalid") from exc

    def _encrypt_secret(self, value: str) -> str:
        if not value:
            return ""
        encrypted = self._get_secret_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{self.IMAP_PASSWORD_PREFIX}{encrypted}"

    def _decrypt_secret(self, value: str) -> str:
        if not value:
            return ""
        if not value.startswith(self.IMAP_PASSWORD_PREFIX):
            return value

        encrypted = value[len(self.IMAP_PASSWORD_PREFIX) :]
        try:
            return self._get_secret_fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError("Unable to decrypt IMAP password with current APP_SECRETS_ENCRYPTION_KEY") from exc

    def _get_profile_row(self, user_id: str, columns: str) -> Optional[Dict]:
        if not user_id:
            return None

        response = (
            get_supabase_service()
            .table("profile")
            .select(columns)
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    def _format_imap_config(self, row: Optional[Dict], include_password: bool = False) -> Dict:
        row = row or {}
        has_password = bool(row.get("imap_password"))
        config = {
            "host": row.get("imap_host") or "",
            "port": row.get("imap_port") or 993,
            "username": row.get("imap_username") or "",
            "mailbox": row.get("imap_mailbox") or "INBOX",
            "use_ssl": bool(row.get("imap_use_ssl", True)),
            "enabled": bool(row.get("imap_enabled", False)),
            "has_password": has_password,
        }
        if include_password:
            config["password"] = self._decrypt_secret(row.get("imap_password") or "")
        return config

    @staticmethod
    def _imap_is_configured(config: Dict) -> bool:
        return bool(config.get("host") and config.get("username") and config.get("has_password"))

    def get_imap_config(self, user_id: str, include_password: bool = False) -> Dict:
        try:
            row = self._get_profile_row(
                user_id,
                "imap_host, imap_port, imap_username, imap_password, imap_mailbox, imap_use_ssl, imap_enabled",
            )
            config = self._format_imap_config(row, include_password=include_password)
            return {
                "status": "ok",
                "configured": self._imap_is_configured(config),
                "config": config,
            }
        except Exception as e:
            print(f"[EmailRepository] Error reading IMAP config: {e}")
            return {"status": "error", "message": f"Error reading IMAP config: {str(e)}"}

    def get_imap_status(self, user_id: str) -> Dict:
        result = self.get_imap_config(user_id)
        if result.get("status") != "ok":
            return result

        config = result.get("config") or {}
        configured = result.get("configured", False)
        enabled = bool(config.get("enabled"))
        return {
            "status": "ok",
            "configured": configured,
            "enabled": enabled,
            "connected": configured and enabled,
            "message": "IMAP configured" if configured else "IMAP not configured",
            "config": config,
        }

    def save_imap_config(self, user_id: str, payload: Dict) -> Dict:
        try:
            if not user_id:
                return {"status": "error", "message": "Missing user_id"}

            existing_result = self.get_imap_config(user_id, include_password=True)
            existing_config = (existing_result.get("config") or {}) if existing_result.get("status") == "ok" else {}

            use_ssl = bool(payload.get("use_ssl", True))
            port_value = payload.get("port")
            try:
                port = int(port_value) if port_value not in (None, "") else (993 if use_ssl else 143)
            except Exception:
                return {"status": "error", "message": "Invalid IMAP port"}

            password = payload.get("password")
            if password in (None, ""):
                password = existing_config.get("password") or ""

            update_data = {
                "imap_host": str(payload.get("host") or "").strip(),
                "imap_port": port,
                "imap_username": str(payload.get("username") or "").strip(),
                "imap_password": self._encrypt_secret(password),
                "imap_mailbox": str(payload.get("mailbox") or "INBOX").strip() or "INBOX",
                "imap_use_ssl": use_ssl,
                "imap_enabled": bool(payload.get("enabled", True)),
            }

            if not update_data["imap_host"] or not update_data["imap_username"] or not update_data["imap_password"]:
                return {"status": "error", "message": "IMAP host, username and password are required"}

            response = (
                get_supabase_service()
                .table("profile")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )
            if not response.data:
                return {"status": "error", "message": "Profile not found for IMAP configuration"}

            return self.get_imap_config(user_id)
        except Exception as e:
            print(f"[EmailRepository] Error saving IMAP config: {e}")
            return {"status": "error", "message": f"Error saving IMAP config: {str(e)}"}

    def clear_imap_config(self, user_id: str) -> Dict:
        try:
            if not user_id:
                return {"status": "error", "message": "Missing user_id"}

            response = (
                get_supabase_service()
                .table("profile")
                .update(
                    {
                        "imap_host": None,
                        "imap_port": None,
                        "imap_username": None,
                        "imap_password": None,
                        "imap_mailbox": None,
                        "imap_use_ssl": True,
                        "imap_enabled": False,
                    }
                )
                .eq("id", user_id)
                .execute()
            )
            if not response.data:
                return {"status": "error", "message": "Profile not found for IMAP configuration"}
            return {"status": "ok", "message": "IMAP configuration removed"}
        except Exception as e:
            print(f"[EmailRepository] Error clearing IMAP config: {e}")
            return {"status": "error", "message": f"Error clearing IMAP config: {str(e)}"}

    def _connect_imap(self, config: Dict):
        host = config.get("host")
        port = int(config.get("port") or (993 if config.get("use_ssl", True) else 143))
        username = config.get("username")
        password = config.get("password")
        mailbox = config.get("mailbox") or "INBOX"

        if config.get("use_ssl", True):
            client = imaplib.IMAP4_SSL(host, port)
        else:
            client = imaplib.IMAP4(host, port)
            client.starttls()

        client.login(username, password)
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            client.logout()
            raise RuntimeError(f"Unable to select mailbox '{mailbox}'")
        return client

    def test_imap_connection(self, user_id: str) -> Dict:
        result = self.get_imap_config(user_id, include_password=True)
        if result.get("status") != "ok":
            return result

        config = result.get("config") or {}
        if not self._imap_is_configured(config):
            return {"status": "error", "message": "IMAP is not fully configured"}

        client = None
        try:
            client = self._connect_imap(config)
            return {"status": "ok", "message": "IMAP connection successful"}
        except Exception as e:
            print(f"[EmailRepository] IMAP connection test failed: {e}")
            return {"status": "error", "message": f"IMAP connection failed: {str(e)}"}
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass

    @staticmethod
    def _decode_mime_header(value: str) -> str:
        if not value:
            return ""
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(part)
        return "".join(decoded_parts)

    def _extract_imap_body(self, message) -> str:
        plain_parts: List[str] = []
        html_parts: List[str] = []

        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue

            disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in disposition.lower():
                continue

            charset = part.get_content_charset() or "utf-8"
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(charset, errors="replace")
            content_type = part.get_content_type()
            if content_type == "text/plain":
                plain_parts.append(text)
            elif content_type == "text/html":
                html_parts.append(text)

        if plain_parts:
            return "\n".join([part.strip() for part in plain_parts if part.strip()]).strip()

        if html_parts:
            parser = EmailHTMLParser()
            for part in html_parts:
                parser.feed(part)
            return parser.get_text().strip()

        return ""

    def _save_imap_email_to_database(self, user_id: str, uid: str, message, username: str) -> Dict:
        raw_from = self._decode_mime_header(message.get("From", ""))
        raw_to = self._decode_mime_header(message.get("To", ""))
        raw_cc = self._decode_mime_header(message.get("Cc", ""))
        subject = self._decode_mime_header(message.get("Subject", ""))
        email_date = message.get("Date") or datetime.now(timezone.utc).isoformat()
        provider_thread_id = message.get("Message-ID")
        body_full = self._extract_imap_body(message)
        body_preview = (body_full[:250] + "...") if len(body_full) > 250 else body_full

        from_email, from_name, from_domain, from_raw, from_is_valid = parse_from_header(raw_from)
        from_local = from_email.split("@")[0] if "@" in from_email else None
        to_email, _, _, _, _ = parse_from_header(raw_to)
        cc_email = raw_cc or None

        account_id = None
        contact_id = None

        try:
            account_id = self._get_or_create_sender_account(from_domain, user_id, from_name)
        except Exception as account_error:
            print(f"[EmailRepository] Warning: failed to resolve sender account: {account_error}")

        if account_id:
            try:
                contact_id = self._get_or_create_sender_contact(from_email, from_name, account_id, user_id)
            except Exception as contact_error:
                print(f"[EmailRepository] Warning: failed to resolve sender contact: {contact_error}")

        return self.db_handler.store_email(
            user_id=user_id,
            provider="imap",
            provider_message_id=uid,
            provider_thread_id=provider_thread_id,
            provider_account_id=username,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            from_raw=from_raw,
            from_domain=from_domain,
            from_local=from_local,
            from_is_valid=from_is_valid,
            to_email=to_email,
            cc_email=cc_email,
            contact_id=contact_id,
            account_id=account_id,
            email_date=email_date,
            body_preview=body_preview,
            body_full=body_full,
            provider_metadata={"mailbox": message.get("X-Original-To") or "INBOX"},
            spf_status="NONE",
            dkim_status="NONE",
            dmarc_status="NONE",
            auth_score=0,
            is_verified=False,
            auth_headers={},
        )

    def fetch_from_imap_and_save(self, user_id: str, max_results: int = 20) -> Dict:
        config_result = self.get_imap_config(user_id, include_password=True)
        if config_result.get("status") != "ok":
            return config_result

        config = config_result.get("config") or {}
        if not self._imap_is_configured(config) or not config.get("enabled"):
            return {
                "status": "error",
                "error_code": "IMAP_NOT_CONFIGURED",
                "message": "IMAP configuration is missing or disabled",
            }

        client = None
        try:
            client = self._connect_imap(config)
            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                return {"status": "error", "message": "Failed to query IMAP mailbox"}

            all_uids = [item.decode("utf-8") for item in (data[0] or b"").split() if item]
            last_fetched_uid = self.db_handler.get_last_fetched_email_id(user_id, provider="imap")
            saved_count = 0
            skipped_count = 0

            for uid in reversed(all_uids):
                if saved_count >= max_results:
                    break
                if last_fetched_uid and uid == last_fetched_uid:
                    break

                fetch_status, message_data = client.uid("fetch", uid, "(RFC822)")
                if fetch_status != "OK" or not message_data:
                    continue

                raw_message = None
                for item in message_data:
                    if isinstance(item, tuple) and len(item) >= 2:
                        raw_message = item[1]
                        break
                if not raw_message:
                    continue

                parsed_message = email.message_from_bytes(raw_message)
                db_result = self._save_imap_email_to_database(
                    user_id=user_id,
                    uid=uid,
                    message=parsed_message,
                    username=config.get("username") or "",
                )
                if db_result.get("success"):
                    if db_result.get("skipped"):
                        skipped_count += 1
                    else:
                        saved_count += 1

            return {
                "success": True,
                "status": "ok",
                "provider": "imap",
                "saved": saved_count,
                "skipped": skipped_count,
                "message": f"Fetched {saved_count} IMAP emails",
            }
        except Exception as e:
            print(f"[EmailRepository] Error fetching IMAP emails: {e}")
            return {"status": "error", "message": f"Error fetching IMAP emails: {str(e)}"}
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass

    def _get_active_fetch_provider(self, user_id: str) -> str:
        imap_result = self.get_imap_config(user_id)
        if imap_result.get("status") == "ok":
            config = imap_result.get("config") or {}
            if imap_result.get("configured") and config.get("enabled"):
                return "imap"
        return "gmail"

    def get_available_fetch_provider(self, user_id: str) -> Optional[str]:
        """Return the configured provider for a user, or None if none is usable."""
        imap_result = self.get_imap_config(user_id)
        if imap_result.get("status") == "ok":
            config = imap_result.get("config") or {}
            if imap_result.get("configured") and config.get("enabled"):
                return "imap"

        gmail_status = self.get_gmail_status(user_id=user_id)
        if gmail_status.get("authorized"):
            return "gmail"

        return None
    
    @staticmethod
    def _clean_email_body(email_body: str, max_length: int = 3000) -> str:
        """Strip HTML tags and truncate email body for LLM processing.
        
        Parameters
        ----------
        email_body : str
            Raw email body (may contain HTML)
        max_length : int
            Maximum length in characters (default 3000 ≈ 750 tokens)
        
        Returns
        -------
        str
            Cleaned and truncated text
        """
        try:
            parser = EmailHTMLParser()
            parser.feed(email_body)
            cleaned = parser.get_text()
            if len(cleaned) > max_length:
                cleaned = cleaned[:max_length] + "..."
            return cleaned
        except Exception as e:
            print(f"[EmailRepository] HTML parsing failed: {e}, truncating original")
            return email_body[:max_length] + "..." if len(email_body) > max_length else email_body
    

    def authorize_gmail(self, redirect_url: str = None) -> Dict:
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
        try:
            credentials_path, token_path = self._get_gmail_paths()
            
            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json"
                }
            
            # Delete existing token to force re-authentication
            if token_path.exists():
                token_path.unlink()
            
            # Create GmailClient which will trigger OAuth flow
            try:
                gmail_client = GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(token_path),
                    redirect_url=redirect_url
                )
                
                # Trigger authentication by getting the service
                gmail_client.get_service()
                
                return {
                    "status": "ok",
                    "message": "Gmail authorization successful"
                }
            
            except Exception as e:
                print(f"[EmailRepository] Gmail authorization error: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "status": "error",
                    "message": f"Authorization failed: {str(e)}"
                }
        
        except Exception as e:
            print(f"[EmailRepository] Error in authorize_gmail: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error during authorization: {str(e)}"
            }

    def _get_profile_token_b64(self, user_id: str) -> Optional[str]:
        try:
            supabase = get_supabase_service()
            response = (
                supabase.table("profile")
                .select("google_token_pickle")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0].get("google_token_pickle")
        except Exception as e:
            print(f"[EmailRepository] Error reading profile token: {e}")
        return None

    def _save_profile_token(self, user_id: str, creds) -> bool:
        try:
            token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
            supabase = get_supabase_service()
            response = (
                supabase.table("profile")
                .update({"google_token_pickle": token_b64})
                .eq("id", user_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            print(f"[EmailRepository] Error saving profile token: {e}")
            return False

    def _clear_profile_token(self, user_id: str) -> bool:
        try:
            supabase = get_supabase_service()
            response = (
                supabase.table("profile")
                .update({"google_token_pickle": None})
                .eq("id", user_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            print(f"[EmailRepository] Error clearing profile token: {e}")
            return False

    def get_gmail_oauth_url(self, redirect_url: str = None, user_id: str = None) -> Dict:
        """Start Gmail OAuth web flow and return the authorization URL."""
        try:
            credentials_path, _ = self._get_gmail_paths()

            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json"
                }

            if not user_id:
                return {"status": "error", "message": "Missing user_id"}

            resolved_redirect_url = redirect_url or _resolve_frontend_redirect_url()
            callback_url = self._resolve_gmail_callback_url(resolved_redirect_url)
            flow = Flow.from_client_secrets_file(
                str(credentials_path),
                scopes=GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(self._get_gmail_paths()[1])
                ).scopes,
                redirect_uri=callback_url,
            )

            state_payload = {
                "redirect_url": resolved_redirect_url,
                "callback_url": callback_url,
                "user_id": user_id,
            }
            state = base64.urlsafe_b64encode(json.dumps(state_payload).encode()).decode()

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
                state=state,
            )

            return {"status": "ok", "auth_url": auth_url}
        except Exception as e:
            print(f"[EmailRepository] Error starting Gmail OAuth: {e}")
            return {"status": "error", "message": f"Error starting Gmail OAuth: {str(e)}"}

    def handle_gmail_oauth_callback(self, code: str, state: str = None) -> Dict:
        """Handle Gmail OAuth callback, exchange code for token, and return redirect URL."""
        try:
            credentials_path, token_path = self._get_gmail_paths()

            if not credentials_path.exists():
                return {
                    "status": "error",
                    "message": "Gmail credentials.json not found. Please add it to var/credentials.json"
                }

            redirect_url = _resolve_frontend_redirect_url()
            callback_url = self._resolve_gmail_callback_url(redirect_url)
            user_id = None
            if state:
                try:
                    decoded = base64.urlsafe_b64decode(state.encode()).decode()
                    payload = json.loads(decoded)
                    redirect_url = payload.get("redirect_url") or redirect_url
                    callback_url = payload.get("callback_url") or self._resolve_gmail_callback_url(redirect_url)
                    user_id = payload.get("user_id")
                except Exception:
                    pass

            flow = Flow.from_client_secrets_file(
                str(credentials_path),
                scopes=GmailClient(
                    credentials_path=str(credentials_path),
                    token_path=str(token_path)
                ).scopes,
                redirect_uri=callback_url,
            )

            flow.fetch_token(code=code)
            creds = flow.credentials

            if user_id:
                self._save_profile_token(user_id, creds)
            else:
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)

            return {"status": "ok", "redirect_url": redirect_url}
        except Exception as e:
            print(f"[EmailRepository] Error handling Gmail OAuth callback: {e}")
            return {"status": "error", "message": f"Error handling Gmail OAuth callback: {str(e)}"}

    def get_gmail_status(self, user_id: str = None) -> Dict:
        """Get Gmail authorization status using the Gmail client validation."""
        try:
            gmail_client, error = self._get_gmail_client(user_id=user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Gmail not authorized")
                }

            try:
                gmail_client.get_service()
            except PermissionError as exc:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": "GMAIL_NOT_AUTHORIZED",
                    "message": str(exc)
                }

            return {
                "status": "ok",
                "authorized": True,
                "message": "Gmail authorized"
            }
        except Exception as e:
            print(f"[EmailRepository] Error checking Gmail status: {e}")
            return {
                "status": "error",
                "authorized": False,
                "message": f"Error checking Gmail status: {str(e)}"
            }

    def revoke_gmail(self, user_id: str = None) -> Dict:
        """Revoke Gmail authorization by deleting token file."""
        try:
            if user_id:
                self._clear_profile_token(user_id)
            else:
                _, token_path = self._get_gmail_paths()
                if token_path.exists():
                    token_path.unlink()
            return {"status": "ok", "message": "Gmail authorization removed"}
        except Exception as e:
            print(f"[EmailRepository] Error revoking Gmail: {e}")
            return {"status": "error", "message": f"Error revoking Gmail: {str(e)}"}

    def get_gmail_profile(self, user_id: str = None) -> Dict:
        """Get Gmail user profile info and granted permissions."""
        try:
            gmail_client, error = self._get_gmail_client(user_id=user_id)
            if error:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": error.get("error_code"),
                    "message": error.get("message", "Gmail not authorized")
                }

            try:
                service = gmail_client.get_service()
            except PermissionError as exc:
                return {
                    "status": "error",
                    "authorized": False,
                    "error_code": "GMAIL_NOT_AUTHORIZED",
                    "message": str(exc)
                }

            profile = service.users().getProfile(userId='me').execute()

            scopes = []
            if user_id:
                token_b64 = self._get_profile_token_b64(user_id)
                if token_b64:
                    try:
                        creds = pickle.loads(base64.b64decode(token_b64.encode("utf-8")))
                        scopes = list(getattr(creds, "scopes", []) or [])
                    except Exception:
                        scopes = []
            else:
                _, token_path = self._get_gmail_paths()
                if token_path.exists():
                    try:
                        with open(token_path, "rb") as token:
                            creds = pickle.load(token)
                            scopes = list(getattr(creds, "scopes", []) or [])
                    except Exception:
                        scopes = []

            if not scopes:
                scopes = list(getattr(gmail_client, "scopes", []) or [])

            return {
                "status": "ok",
                "authorized": True,
                "profile": profile,
                "permissions": scopes,
            }
        except Exception as e:
            print(f"[EmailRepository] Error fetching Gmail profile: {e}")
            return {
                "status": "error",
                "authorized": False,
                "message": f"Error fetching Gmail profile: {str(e)}"
            }
        
    def getEmail(self, email_id: str) -> Optional[Dict]:
        """Get a single email by ID."""
        email = self.db_handler.get_email(email_id)
        if not email:
            return {
                "status": "error",
                "message": f"Email not found: {email_id}"
            }
        
        # Handle email as dict or tuple
        if isinstance(email, (list, tuple)):
            if len(email) == 0:
                return {
                    "status": "error",
                    "message": f"Email not found: {email_id}"
                }
            email = email[0] if isinstance(email, list) else email
        
        # Ensure email is a dict
        if not isinstance(email, dict):
            return {
                "status": "error",
                "message": f"Invalid email format: {type(email)}"
            }
        
    def generate_account_from_email(self, email: Dict) -> str:  
        """Generate or find account for email sender.
        
        Creates account first, then ensures contact exists.
        Raises exception if contact creation fails to prevent orphaned accounts.
        """
        from_email = email.get("from_email", "") or email.get("from", "")
        from_name = email.get("from_name", "")
        
        if not from_email:
            raise ValueError("Cannot create account/contact without email address")
        
        # Use Supabase service client
        supabase = get_supabase_service()
        
        # Step 1: Check if contact already exists (reuse existing account if so)
        try:
            existing_contacts = supabase.table("contact").select("*, account:account_id(id, name)").eq("email", from_email).limit(1).execute()
            if existing_contacts.data and len(existing_contacts.data) > 0:
                contact = existing_contacts.data[0]
                account_id = contact.get("account_id")
                print(f"[EmailRepository] Found existing contact {contact.get('id')} with account {account_id}")
                return account_id
        except Exception as e:
            print(f"[EmailRepository] Warning: Error checking existing contact: {e}")
        
        # Step 2: Create account (required for contact.account_id foreign key)
        company_name = from_name or from_email.split("@")[1] if "@" in from_email else "Unknown Company"
        
        try:
            account_data = {"name": company_name}
            account_response = supabase.table("account").insert(account_data).execute()
            if not account_response.data or len(account_response.data) == 0:
                raise ValueError("Account creation returned no data")
            
            account_id = account_response.data[0]["id"]
            print(f"[EmailRepository] Created new account: {account_id} ({company_name})")
        except Exception as e:
            print(f"[EmailRepository] Error creating account: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to create account: {str(e)}")
        
        # Step 3: Create contact (REQUIRED - if this fails, rollback should happen)
        try:
            contact_data = {
                "name": from_name or from_email,
                "email": from_email,
                "account_id": account_id,
            }
            contact_response = supabase.table("contact").insert(contact_data).execute()
            if not contact_response.data or len(contact_response.data) == 0:
                # Critical failure - account exists but contact creation failed
                # Delete the orphaned account
                try:
                    supabase.table("account").delete().eq("id", account_id).execute()
                    print(f"[EmailRepository] Rolled back orphaned account {account_id}")
                except Exception as rollback_error:
                    print(f"[EmailRepository] Warning: Failed to rollback account {account_id}: {rollback_error}")
                
                raise ValueError("Contact creation returned no data")
            
            contact_id = contact_response.data[0]["id"]
            print(f"[EmailRepository] Created new contact: {contact_id} for {from_email}")
            
        except Exception as e:
            print(f"[EmailRepository] CRITICAL: Contact creation failed for account {account_id}: {e}")
            # Try to clean up orphaned account
            try:
                supabase.table("account").delete().eq("id", account_id).execute()
                print(f"[EmailRepository] Rolled back orphaned account {account_id}")
            except Exception as rollback_error:
                print(f"[EmailRepository] ERROR: Failed to rollback account {account_id}: {rollback_error}")
            
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to create contact for account {account_id}: {str(e)}")
        
        return account_id
    
    def create_opportunity_from_email(self, message_id, user_id) -> Dict:
        supabase = get_supabase_service()
        email = self.db_handler.get_email(message_id)
        print(f"[EmailRepository] Email result type: {type(email)}, value: {email}")
        
        if not email:
            return {
                "status": "error",
                "message": "Email not found"
            }
        
        # Step 1: Extract email content
        email_body = email.get("body_full") or email.get("body_preview") or ""
        from_email = email.get("from_email", "")
        from_name = email.get("from_name", "")
        email_body_clean = self._clean_email_body(email_body)
        print(f"[EmailRepository] Email body cleaned: {len(email_body)} → {len(email_body_clean)} chars")
            
        # Step 2: Extract RFP/contact data from email body
        print(f"[EmailRepository] Extracting RFP from email: {len(email_body)} → {len(email_body_clean)} chars")
        rfp_data = extract_rfp_from_text(email_body_clean)
        print(f"[EmailRepository] RFP data type: {type(rfp_data)}, value: {rfp_data}")
        
        # Step 3: Generate account and contact
        account_id = self.generate_account_from_email(email)
        
        # Step 4: Build opportunity data
        opportunity_name = rfp_data.get('title') or f"Requete {from_name or from_email}"
        email_category = email.get("category") or "Other"
        
        # Map email category to opportunity stage
        stage_mapping = {
            "RFQ": "RFQ_IN_PROGRESS",
            "RFP": "RFP_IN_PROGRESS",
            "RFI": "NEEDS_DEFINED",
            "Quote": "OFFER_SENT",
            "Proposal": "OFFER_SENT",
            "Other": "NEW_LEAD"
        }
        opportunity_stage = stage_mapping.get(email_category, "NEW_LEAD")
        
        # Insert into opportunity table via Supabase
        opportunity_insert_data = {
            "owner_user_id": user_id,
            "account_id": account_id,
            "name": opportunity_name,
            "stage": opportunity_stage,
            "status": "OPEN",
            "source": "email",
            "source_reference_id": message_id
        }
        
        print(f"[EmailRepository] Creating opportunity with data: {opportunity_insert_data}")
        result = supabase.table("opportunity").insert(opportunity_insert_data).execute()
        
        if not result.data:
            return {
                "status": "error",
                "message": "Failed to create opportunity in Supabase"
            }
        
        opportunity_id = result.data[0]["id"]
        
        print(f"[EmailRepository] Opportunity created successfully: {opportunity_id}")
        return {
            "status": "ok",
            "opportunity": {
                "id": opportunity_id,
                "name": opportunity_name,
                "stage": opportunity_stage,
                "status": "OPEN",
                "account_id": account_id,
                "message": f"Opportunity created successfully from {email_category}"
            }
        }
    
    def fetch_emails(self, user_id: str, max_results: int = 20, force: bool = False, classify: bool = True) -> Dict:
        """List messages from Gmail inbox and optionally save to database.
        Only fetches from Gmail if force=True. Otherwise, displays cached results from database.
        
        Parameters
        ----------
        user_id : str
            Supabase user ID for saving emails to database
        max_results : int
            Maximum number of messages to return
        force : bool
            Force fetch from Gmail API, bypassing cache
        classify : bool
            If True and force=True, also classify emails and create contacts/accounts
        
        Returns
        -------
        Dict
            Response with list of messages and processing summary
        """
        try:
            if not user_id:
                raise ValueError("user_id is required to fetch emails")
            
            processing_summary = None
            provider = self._get_active_fetch_provider(user_id)
            
            # Only fetch from Gmail if force=true, otherwise just return cached DB results
            if force:
                if classify:
                    print(f"[EmailRepository] → Fetching via {provider}, classifying, and linking contacts (full refresh)")
                    processing_summary = self.fetch_and_process_emails(user_id, max_results=max_results)
                else:
                    print(f"[EmailRepository] → Fetching emails from {provider.upper()} (force refresh)")
                    if provider == "imap":
                        self.fetch_from_imap_and_save(user_id, max_results=max_results)
                    else:
                        self.fetch_from_gmail_and_save(user_id, max_results=max_results)
            else:
                print(f"[EmailRepository] ✓ Using existing emails from DATABASE (no refresh)")
            
            messages = self._get_user_emails(user_id, limit=max_results)
            
            response = {
                "status": "ok",
                "messages": messages,
                "total": len(messages),
                "force_refreshed": force,
                "provider": provider,
            }
            
            # Include processing summary if we did full workflow
            if processing_summary:
                response["processing"] = processing_summary
            
            return response
        except Exception as e:
            print(f"[EmailRepository] Error fetching emails: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    def _parse_after_date(self, value: str) -> datetime:
        """Parse an email_date value into a datetime."""
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return parsedate_to_datetime(value)
    
    def _to_epoch_seconds(self, dt: datetime) -> int:
        """Convert datetime to Unix epoch seconds."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    
    def _resolve_after_date(self, user_id: str, provided_after_date: str | None) -> str | None:
        """Resolve after-date for Gmail query, defaulting to latest email + 1 second.
        
        Parameters
        ----------
        user_id : str
            User ID to query latest email for
        provided_after_date : str, optional
            Explicitly provided after-date (takes precedence)
        
        Returns
        -------
        str
            Epoch seconds string for Gmail query, or None
        """
        if provided_after_date:
            return provided_after_date
        
        latest = self.db_handler.get_emails_by_user(user_id, limit=1)
        if latest:
            email_date = latest[0].get("email_date")
            if email_date:
                try:
                    parsed = self._parse_after_date(email_date)
                    # Add 1 second to avoid reprocessing the most recent email
                    return str(self._to_epoch_seconds(parsed) + 1)
                except Exception:
                    pass
        
        # Fallback to yesterday (epoch seconds)
        from datetime import timedelta
        fallback = datetime.now(timezone.utc) - timedelta(days=1)
        return str(self._to_epoch_seconds(fallback))
    
    def fetch_and_process_emails(
        self, 
        user_id: str, 
        max_results: int = 50, 
        classify_limit: int = 200,
        after_date: str = None,
        auto_resolve_date: bool = False
    ) -> Dict:
        """Comprehensive email processing: fetch, classify, create contacts/accounts.
        
        This method performs the complete email workflow:
        1. Fetches emails from Gmail API (with optional date filtering)
        2. Classifies unclassified emails using AI
        3. Creates contacts and accounts from sender information
        4. Links emails to contacts and accounts
        
        Parameters
        ----------
        user_id : str
            Supabase user ID
        max_results : int
            Maximum number of emails to fetch from Gmail
        classify_limit : int
            Maximum number of unclassified emails to classify
        after_date : str, optional
            Fetch emails after this date (YYYY/MM/DD or Unix seconds)
        auto_resolve_date : bool
            If True and after_date is None, automatically resolve to latest email + 1 second
        
        Returns
        -------
        Dict
            Summary with counts: emails_fetched, emails_classified, contacts_created, accounts_created
        """
        
        # Auto-resolve after-date if enabled
        if auto_resolve_date and not after_date:
            after_date = self._resolve_after_date(user_id, after_date)
            if after_date:
                print(f"[EmailRepository] Auto-resolved after-date to: {after_date} (epoch seconds)")
        
        result = {
            "status": "ok",
            "user_id": user_id,
            "provider": self._get_active_fetch_provider(user_id),
            "emails_fetched": 0,
            "emails_classified": 0,
            "contacts_created": 0,
            "accounts_created": 0,
            "rfq_processed": 0,
            "opportunities_created": 0,
            "quotes_generated": 0,
            "errors": [],
            "after_date_used": after_date
        }
        
        try:
            provider = result["provider"]
            # Step 1: Fetch emails from configured provider
            print(f"[EmailRepository] Fetching emails from {provider}...")
            if provider == "imap":
                fetch_result = self.fetch_from_imap_and_save(
                    user_id=user_id,
                    max_results=max_results,
                )
            else:
                fetch_result = self.fetch_from_gmail_and_save(
                    user_id=user_id,
                    max_results=max_results,
                    before_date=after_date,
                )
            
            if not fetch_result.get("success"):
                error_msg = fetch_result.get('message', 'Unknown error')
                result["errors"].append(f"Fetch failed: {error_msg}")
                result["status"] = "error"
                return result

            result["emails_fetched"] = int(fetch_result.get("saved") or 0)
            
            print(f"[EmailRepository] ✓ Fetched emails successfully")
            
            supabase = get_supabase_service()
            # Get recent emails to process
            
            # Step 2: Classify unclassified emails
            try:
                print(f"[EmailRepository] Classifying emails...")
                classify_result = self.classify_unclassified_emails(user_id=user_id, limit=classify_limit)
                result["emails_classified"] = classify_result.get("classified", 0)
                result["rfq_processed"] = classify_result.get("rfq_processed", 0)
                result["opportunities_created"] = classify_result.get("opportunities_created", 0)
                result["quotes_generated"] = classify_result.get("quotes_generated", 0)
                
                if classify_result.get("errors"):
                    result["errors"].extend(classify_result.get("errors", []))
                if classify_result.get("auto_action_errors"):
                    result["errors"].extend(classify_result.get("auto_action_errors", []))
                
                print(f"[EmailRepository] ✓ Classified {result['emails_classified']} emails")
            except Exception as e:
                print(f"[EmailRepository] Warning: Classification failed: {e}")
                result["errors"].append(f"Classification error: {str(e)}")
            
            
            return result
        
        except Exception as e:
            print(f"[EmailRepository] Error in fetch_and_process_emails: {e}")
            import traceback
            traceback.print_exc()
            result["status"] = "error"
            result["errors"].append(str(e))
            return result
    
    def get_contact_by_email(self, email_list: List[str], user_id: str) -> Dict:    
        from src.infrastructure.clients.supabase import get_supabase_service
        supabase = get_supabase_service()
        for email in email_list:
            fetch_result = supabase.table("email").select("from_email").eq("user_id", user_id).eq("from_email", email).limit(1).execute()
            if fetch_result.data and len(fetch_result.data) > 0:
                return
        
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str = None,
        cc: str = None,
        bcc: str = None,
        user_id: str = None,
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
        try:
            try:
                gmail_client, error = self._get_gmail_client(user_id=user_id)
                if error:
                    return error
                
                result = gmail_client.send_email_with_attachment(
                    to=to,
                    subject=subject,
                    body=body,
                    attachment_path=attachment_path,
                    cc=cc,
                    bcc=bcc
                )
                
                return {
                    "status": "ok",
                    "message": "Email sent successfully",
                    "provider": "gmail",
                    "message_id": result.get('message_id')
                }
            
            except PermissionError as e:
                error_msg = str(e)
                if "GMAIL_AUTH_ERROR:" in error_msg:
                    return {
                        "status": "error",
                        "error_code": "GMAIL_AUTH_ERROR",
                        "message": error_msg.replace("GMAIL_AUTH_ERROR:", "").strip()
                    }
                elif "GMAIL_PERMISSION_ERROR:" in error_msg:
                    return {
                        "status": "error",
                        "error_code": "GMAIL_PERMISSION_ERROR",
                        "message": error_msg.replace("GMAIL_PERMISSION_ERROR:", "").strip()
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Permission error: {error_msg}"
                    }
        
        except Exception as e:
            print(f"[EmailRepository] Error sending email: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error sending email: {str(e)}"
            }
    
    def get_message_body(self, uuid: str, user_id: str) -> Dict:
        """Get the full content of a message.
        
        Parameters
        ----------
        uuid : str
            ID of the message to fetch
        user_id : str
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with full message content
        """
        if not user_id:
            return {
                "status": "error",
                "message": "User not authenticated"
            }

        message_record = self.db_handler.get_email(uuid)
        if not message_record:
            return {
                "status": "error",
                "message": f"Message with id {uuid} not found"
            }
        
        # Verify ownership: email must belong to the authenticated user
        if message_record.get('user_id') != user_id:
            return {
                "status": "error",
                "message": "Unauthorized"
            }
        
        opportunities = []
        try:
            supabase = get_supabase_service()
            response = (
                supabase.table("opportunity")
                .select("id, name, stage, status, account_id, source_reference_id")
                .eq("owner_user_id", user_id)
                .eq("source_reference_id", uuid)
                .execute()
            )
            opportunities = response.data or []
        except Exception as exc:  # pragma: no cover
            print(f"[EmailRepository] Error loading opportunities for email {uuid}: {exc}")

        return {
            "status": "ok",
            "message": message_record.get('body_full'),
            "opportunities": opportunities,
        }
    
    def classify_email(self, email_uuid: str, user_id: str, force: bool = False) -> Dict:
        """Classify an email and store the result.
        
        Parameters
        ----------
        email_uuid : str
            The UUID of the email to classify
        user_id : str
            The user ID (for authorization)
        
        Returns
        -------
        dict
            Response with status, message, and classification result
        """
        try:
            
            print(f"[EmailRepository] Attempting to classify email: {email_uuid} for user: {user_id} (force={force})")
            
            # Get email from database
            email = self.db_handler.get_email(email_uuid)
            print(f"[EmailRepository] Email lookup result: {email is not None}")
            if email:
                print(f"[EmailRepository] Email data keys: {list(email.keys())}")
            
            if not email:
                print(f"[EmailRepository] Email not found: {email_uuid} for user: {user_id}")
                return {
                    "status": "error",
                    "error_code": "EMAIL_NOT_FOUND",
                    "message": f"Email not found: {email_uuid}"
                }

            # Verify ownership
            if user_id and email.get("user_id") != user_id:
                print(f"[EmailRepository] Unauthorized access: email {email_uuid} not owned by user {user_id}")
                return {
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "Unauthorized"
                }

            # Skip classification if already classified; re-map stored fields to expected keys
            if email.get("is_classified") and not force:
                print(f"[EmailRepository] Email already classified, returning cached result")
                classification = {
                    "category": email.get("category"),
                    "new_category": email.get("category_suggestion"),
                    "reason": email.get("classification_reason"),
                    "important": email.get("important", False),
                }
            else:
                # Extract email content
                subject = email.get("subject", "")
                body = email.get("body_full") or email.get("body_preview", "")

                from_email = email.get("from_email", "")
                
                # Truncate body to avoid context overflow (max ~2000 tokens ≈ 8000 chars)
                # This leaves room for system prompt, subject, and response
                max_body_length = 30000
                if len(body) > max_body_length:
                    #print(f"[EmailRepository] Truncating body from {len(body)} to {max_body_length} chars")
                    #body = body[:max_body_length] + "... [truncated]"
                    print(f"[EmailRepository] stripping html from body from {len(body)} over {max_body_length} chars (has {len(body)} chars)")
                    body = self._clean_email_body(body, max_length=max_body_length)
                    print(f"[EmailRepository] body length after cleaning: {len(body)} chars")

                    if len(body) > max_body_length:
                        print(f"[EmailRepository] Truncating cleaned body from {len(body)} to {max_body_length} chars")
                        body = body[:max_body_length] + "... [truncated]"
                
                # Classify using LLM
                classifier = EmailClassifier()
                classification = classifier.classify(
                    title=subject,
                    body=body,
                    from_email=from_email
                )

                print(f"[EmailRepository] Classification result: {classification.get('category')} updating category,new_category,reason and important for email uuid {email_uuid}")

                # Update email in database
                update_result = self.db_handler.update_email_classification(
                    email_uuid=email_uuid,
                    user_id=user_id,
                    category=classification.get("category"),
                    category_suggestion=classification.get("new_category"),
                    classification_reason=classification.get("reason"),
                    is_classified=True,
                    important=classification.get("important", False),
                    classified_at=datetime.now().isoformat()
                )
                print(f"[EmailRepository] Email classification updated: {update_result}")

            return {
                "status": "ok",
                "message": "Email classified successfully",
                "result": {
                    "category": classification.get("category"),
                    "category_suggestion": classification.get("new_category"),
                    "classification_reason": classification.get("reason"),
                    "classified_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            print(f"[ERROR] Classification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "CLASSIFICATION_ERROR",
                "message": f"Classification failed: {str(e)}"
            }

    def classify_unclassified_emails(self, user_id: str, limit: int = 200) -> Dict:
        """Classify emails that have not yet been classified."""
        pending = self.db_handler.get_unclassified_emails(user_id, limit=limit)
        if not pending:
            return {
                "status": "ok",
                "classified": 0,
                "skipped": 0,
                "errors": [],
                "rfq_processed": 0,
                "opportunities_created": 0,
                "quotes_generated": 0,
            }

        classified = 0
        skipped = 0
        errors: List[Dict] = []
        rfq_processed = 0
        opportunities_created = 0
        quotes_generated = 0
        auto_action_errors: List[Dict] = []

        for email in pending:
            email_id = email.get("id")
            try:
                result = self.classify_email(email_id, user_id)
                if result.get("status") == "ok":
                    classified += 1
                    # Auto-create opportunity + quote for RFQ emails
                    classification = result.get("result", {}) or {}
                    category = classification.get("category") or classification.get("new_category")
                    if isinstance(category, str) and category.strip().upper() == "RFQ":
                        rfq_processed += 1
                        auto_result = self._auto_create_opportunity_and_quote(email_id, user_id)
                        if auto_result.get("status") == "ok":
                            if auto_result.get("opportunity_created"):
                                opportunities_created += 1
                            if auto_result.get("quote_generated"):
                                quotes_generated += 1
                        elif auto_result.get("status") == "skipped":
                            # already had opportunity
                            pass
                        else:
                            auto_action_errors.append({
                                "email_id": email_id,
                                "error": auto_result,
                            })
                else:
                    skipped += 1
                    errors.append({"email_id": email_id, "error": result})
            except Exception as exc:  # pragma: no cover
                skipped += 1
                errors.append({"email_id": email_id, "error": str(exc)})

        return {
            "status": "ok",
            "classified": classified,
            "skipped": skipped,
            "errors": errors,
            "rfq_processed": rfq_processed,
            "opportunities_created": opportunities_created,
            "quotes_generated": quotes_generated,
            "auto_action_errors": auto_action_errors,
        }

    def _auto_create_opportunity_and_quote(self, email_id: str, user_id: str) -> Dict:
        """Create opportunity + generate quote for RFQ emails during fetch/classify.
        
        Scans both email body and PDF attachments for products, uses whichever has most products.
        """
        from src.infrastructure.clients.supabase import get_supabase_service
        from pathlib import Path
        import json
        from src.lib.extractors.rfp_source_picker import pick_best_rfp_source


        try:
            supabase = get_supabase_service()

            # Avoid duplicates: check existing opportunity linked to this email
            existing = (
                supabase.table("opportunity")
                .select("id")
                .eq("source_reference_id", email_id)
                .eq("owner_user_id", user_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                return {
                    "status": "skipped",
                    "reason": "opportunity_already_exists",
                    "opportunity_id": existing.data[0].get("id"),
                }

            # Get email body
            email = self.db_handler.get_email(email_id)
            if not email:
                return {
                    "status": "error",
                    "step": "load_email",
                    "details": "Email not found",
                }

            email_body = email.get("body_full") or email.get("body_preview") or ""
            
            # Get PDF attachments
            pdf_attachment_id = None
            pdf_attachments = []
            try:
                attachments_response = supabase.table("email_attachment").select(
                    "id, filename, mime_type, storage_path"
                ).eq("email_id", email_id).execute()
                
                pdf_attachments = [
                    att for att in (attachments_response.data or [])
                    if att.get("mime_type") == "application/pdf"
                ]
                
                print(f"[EmailRepository] Found {len(pdf_attachments)} PDF attachments")
                
            except Exception as e:
                print(f"[EmailRepository] Error getting PDF attachments: {e}")

            # Decide which source to use (most products wins)
            pdf_candidates = [
                {
                    "id": att.get("id"),
                    "filename": att.get("filename"),
                    "path": Path(att.get("storage_path")) if att.get("storage_path") else None,
                }
                for att in (pdf_attachments or [])
                if att.get("mime_type") == "application/pdf"
            ]
            selection = pick_best_rfp_source(email_body, pdf_candidates)
            best_source = selection.get("source", "text")
            product_count = selection.get("product_count", 0)
            pdf_attachment_id = selection.get("pdf_attachment_id")
            best_content = selection.get("content", email_body)
            if best_source == "pdf":
                print(f"[EmailRepository] Using PDF attachment (most products: {product_count})")
            else:
                print(f"[EmailRepository] Using email body (most products: {product_count})")

            # Create opportunity directly via repository/service layer.
            from src.repository.opportunity import OpportunityRepository

            opportunity_repository = OpportunityRepository()

            create_result = self.create_opportunity_from_email(
                message_id=email_id,
                user_id=user_id,
            )
            if create_result.get("status") != "ok":
                return {
                    "status": "error",
                    "step": "create_opportunity",
                    "details": create_result,
                }

            opportunity = create_result.get("opportunity", {}) or {}
            opportunity_id = opportunity.get("id")
            if not opportunity_id:
                return {
                    "status": "error",
                    "step": "create_opportunity",
                    "details": "Missing opportunity id",
                }

            # Generate quote using the best source
            if best_source == "pdf" and best_content:
                quote_result = opportunity_repository.handle_generate_quote_with_content(
                    opportunity_id=opportunity_id,
                    content=best_content,
                    user_id=user_id,
                    pre_extracted_data=selection.get("extracted_data"),  # Avoid re-extraction
                )
            else:
                quote_result = opportunity_repository.handle_generate_quote_for_opportunity(
                    opportunity_id=opportunity_id,
                    user_id=user_id,
                )

            quote_ok = quote_result.get("status") == "ok"
            return {
                "status": "ok" if quote_ok else "error",
                "opportunity_created": True,
                "quote_generated": quote_ok,
                "opportunity_id": opportunity_id,
                "quote_result": quote_result,
                "source_used": best_source,
                "product_count": product_count,
                "pdf_attachment_id": pdf_attachment_id if best_source == "pdf" else None,
            }

        except Exception as exc:  # pragma: no cover
            print(f"[EmailRepository] Auto opportunity/quote error: {exc}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "step": "exception",
                "details": str(exc),
            }
    
    
    def fetch_from_gmail_and_save(self, user_id: str, max_results: int = 20, before_date: str = None) -> Dict:
        """Fetch emails from Gmail and save to database.
        
        Fetches all new emails until reaching the last fetched email ID.
        Automatically paginates through results if needed.
        
        When before_date is specified, fetches ALL emails in that date range
        (ignoring last_fetched_email_id for comprehensive re-fetch).
        """
        gmail_client, error = self._get_gmail_client(user_id=user_id)
        if error:
            return error
        
        try:
            
            # Get last fetched email ID to determine stopping point
            # Skip this check if before_date is explicitly provided (user wants full date range)
            last_fetched_email_id = None if before_date else self.db_handler.get_last_fetched_email_id(user_id, provider="gmail")
            
            print(f"[EmailRepository] Last fetched email ID: {last_fetched_email_id}")
            
            # Build Gmail query for date limit (oldest email = start date)
            query = None
            if before_date:
                # Convert to "after" query: emails from this date onwards
                query = f"after:{before_date}"
                print(f"[EmailRepository] Date limit (oldest email): {before_date}")
                print(f"[EmailRepository] Fetching ALL emails since {before_date} (ignoring duplicate detection)")
            
            # Fetch all new emails with pagination, with a hard global cap.
            max_total_fetch = int(os.getenv("GMAIL_MAX_TOTAL_FETCH", "100"))
            page_token = None
            found_last_email = False
            reached_fetch_limit = False
            page_count = 0
            inspected_count = 0
            seen_page_tokens = set()
            
            saved_count = 0
            skipped_count = 0
            db_result = {"success": True}
            
            while not found_last_email and not reached_fetch_limit:
                page_count += 1
                print(f"[EmailRepository] Fetching page {page_count}...")

                # Guard against buggy/repeating pagination tokens.
                if page_token and page_token in seen_page_tokens:
                    print("[EmailRepository] Detected repeated nextPageToken; stopping pagination to avoid loop")
                    break
                if page_token:
                    seen_page_tokens.add(page_token)

                remaining_budget = max_total_fetch - inspected_count
                if remaining_budget <= 0:
                    print(f"[EmailRepository] Reached fetch cap before next page: {max_total_fetch}")
                    break
                
                result = gmail_client.list_messages(
                    max_results=min(max_results, remaining_budget),
                    page_token=page_token,
                    query=query
                )
                
                messages = result.get('messages', [])
                if not messages:
                    print(f"[EmailRepository] No more messages to fetch")
                    break
                
                # Check each message to see if we've reached the last fetched email
                for message in messages:
                    if last_fetched_email_id and message['id'] == last_fetched_email_id:
                        print(f"[EmailRepository] Reached last fetched email (ID: {last_fetched_email_id})")
                        found_last_email = True
                        break

                    inspected_count += 1
                    
                    db_result = self._save_email_to_database(gmail_client, message, user_id)
                    
                    if db_result.get('success'):
                        if db_result.get('skipped'):
                            skipped_count += 1
                        else:
                            saved_count += 1
                    else:
                        print(f"[EmailRepository] Failed to save email {message.get('id')}: {db_result.get('error')}")

                    if inspected_count >= max_total_fetch:
                        print(f"[EmailRepository] Reached fetch cap: {max_total_fetch} emails inspected")
                        reached_fetch_limit = True
                        break
                
                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token:
                    print(f"[EmailRepository] No more pages available")
                    break
            
            print(f"[EmailRepository] Fetched across {page_count} page(s)")
            print(
                f"[EmailRepository] Saved {saved_count} new, skipped {skipped_count} duplicate emails "
                f"(inspected {inspected_count}, cap {max_total_fetch})"
            )
            return db_result
        
        except PermissionError as e:
            error_msg = str(e)
            if "GMAIL_AUTH_ERROR:" in error_msg or "GMAIL_PERMISSION_ERROR:" in error_msg:
                return {
                    "status": "error",
                    "error_code": "GMAIL_NOT_AUTHORIZED",
                    "message": "Gmail authorization required"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Permission error: {error_msg}"
                }
    
    def _save_email_to_database(self, gmail_client: GmailClient, message: Dict, user_id: str) -> Dict:
        
        
        """Save a single email message to the database with authentication verification."""
        from src.service.email.email_auth_parser import parse_email_auth
        from src.service.email.email_auth_service import EmailAuthService
        
        # Check if email already exists to avoid duplicate attachments
        provider_message_id = message.get('id')
        try:
            existing = self.db_handler.supabase.table('email').select('id').eq(
                'user_id', user_id
            ).eq('provider_message_id', provider_message_id).limit(1).execute()
            
            if existing.data and len(existing.data) > 0:
                print(f"[EmailRepository] Email already exists: {provider_message_id}, skipping")
                return {"success": True, "skipped": True}
        except Exception as e:
            print(f"[EmailRepository] Warning: Failed to check existing email: {e}")
            raise e
        body_result = gmail_client.get_message_body(message.get('id'))
        body = body_result.get('body', '')
        
        # Parse from field using mime parser
        from_email, from_name, from_domain, from_raw, from_is_valid = parse_from_header(message.get('from', ''))
        from_local = from_email.split('@')[0] if '@' in from_email else None
        
        # Parse to field
        to_email, to_name, _, _, _ = parse_from_header(message.get('to', ''))
        
        # Parse CC field
        cc_raw = message.get('cc', '')
        cc_email = cc_raw if cc_raw else None
        
        
        account_id = self._get_or_create_sender_account(from_domain, user_id, from_name)
        contact_id = self._get_or_create_sender_contact(from_email, from_name, account_id, user_id)
        
        # Extract authentication information
        auth_info = parse_email_auth(message)
        spf_status = auth_info.get("spf_status", "NONE")
        dkim_status = auth_info.get("dkim_status", "NONE")
        dmarc_status = auth_info.get("dmarc_status", "NONE")
        auth_score = auth_info.get("auth_score", 0)
        is_verified = auth_info.get("is_verified", False)
        auth_headers = auth_info.get("auth_headers", {})
        
        print(f"[EmailRepository] Auth check: SPF={spf_status} DKIM={dkim_status} DMARC={dmarc_status} Score={auth_score}")
        
        db_result = self.db_handler.store_email(
            user_id=user_id,
            provider="gmail",
            provider_message_id=message.get('id'),
            provider_thread_id=message.get('threadId'),
            subject=message.get('subject', ''),
            from_email=from_email,
            from_name=from_name,
            from_raw=from_raw,
            from_domain=from_domain,
            from_local=from_local,
            from_is_valid=from_is_valid,
            to_email=to_email,
            cc_email=cc_email,
            contact_id=contact_id,
            account_id=account_id,
            email_date=message.get('date', ''),
            body_preview=message.get('snippet', ''),
            body_full=body,
            category=message.get('category'),
            classification_reason=message.get('classification_reason'),
            spf_status=spf_status,
            dkim_status=dkim_status,
            dmarc_status=dmarc_status,
            auth_score=auth_score,
            is_verified=is_verified,
            auth_headers=auth_headers,
        )
        
        # Verify sender and update trust score
        if db_result.get('success'):
            try:
                auth_handler = EmailAuthService()
                auth_handler.verify_sender(
                    user_id=user_id,
                    sender_email=from_email,
                    sender_name=from_name or from_email,
                    auth_score=auth_score,
                    is_verified=is_verified,
                    spf_status=spf_status,
                    dkim_status=dkim_status,
                    dmarc_status=dmarc_status
                )
            except Exception as e:
                print(f"[EmailRepository] Warning: Failed to verify sender: {e}")
        
        # Save email labels if email was successfully stored
        if db_result.get('success'):
            email_id = db_result.get('email_id')

            if message.get('labels'):
                labels = [
                    {
                        'provider_label_id': label_id,
                        'label_name': label_id
                    }
                    for label_id in message.get('labels', [])
                ]
                
                label_result = self.db_handler.add_labels(email_id, labels)
                if not label_result.get('success'):
                    print(f"[EmailRepository] Warning: Failed to save labels for email {email_id}: {label_result.get('error')}")
                else:
                    print(f"[EmailRepository] Saved {label_result.get('labels_added', 0)} labels for email {email_id}")

            # Download and store attachments
            attachments = message.get('attachments') or []
            if attachments:
                attachments_root = Path(__file__).resolve().parents[2] / "var" / "attachments" / user_id / message.get('id', 'unknown')
                saved = 0
                skipped = 0
                attachment_records = []
                for attachment in attachments:
                    attachment_id = attachment.get('attachmentId') or attachment.get('id')
                    if not attachment_id:
                        continue
                    filename = attachment.get('filename') or f"attachment-{attachment_id}"
                    
                    # Check if attachment already exists in database
                    existing_attachment = None
                    try:
                        response = self.db_handler.supabase.table('email_attachment').select(
                            'id, storage_path'
                        ).eq('email_id', email_id).eq('provider_attachment_id', attachment_id).limit(1).execute()
                        
                        if response.data and len(response.data) > 0:
                            existing_attachment = response.data[0]
                    except Exception as e:
                        print(f"[EmailRepository] Warning: failed to check existing attachment: {e}")
                    
                    # Skip download if attachment already exists and file is present
                    if existing_attachment:
                        existing_path = existing_attachment.get('storage_path')
                        if existing_path and Path(existing_path).exists():
                            print(f"[EmailRepository] Skipping existing attachment: {filename}")
                            skipped += 1
                            # Still add to records for upsert (ensures consistency)
                            attachment_records.append(
                                {
                                    "provider_attachment_id": attachment_id,
                                    "filename": filename,
                                    "mime_type": attachment.get('mimeType'),
                                    "size": attachment.get('size'),
                                    "storage_path": existing_path,
                                }
                            )
                            continue
                    
                    # Download attachment
                    try:
                        file_path = gmail_client.download_attachment(
                            message_id=message.get('id'),
                            attachment_id=attachment_id,
                            dest_dir=attachments_root,
                            filename=filename,
                        )
                        # Deduplicate if filename already exists (handles multiple attachments with same name)
                        file_path = _dedupe_path(file_path)
                        if file_path.parent / filename != file_path:
                            # Path was changed due to duplicate, rename the file
                            (attachments_root / filename).rename(file_path)
                        saved += 1
                        attachment_records.append(
                            {
                                "provider_attachment_id": attachment_id,
                                "filename": filename,
                                "mime_type": attachment.get('mimeType'),
                                "size": attachment.get('size'),
                                "storage_path": str(file_path),
                            }
                        )
                        print(f"[EmailRepository] Saved attachment to {file_path}")
                    except Exception as exc:  # pragma: no cover
                        print(f"[EmailRepository] Warning: failed to save attachment {filename} for email {email_id}: {exc}")

                if attachment_records:
                    attachment_result = self.db_handler.add_attachments(email_id, attachment_records)
                    if not attachment_result.get('success'):
                        print(
                            f"[EmailRepository] Warning: Failed to record attachments for email {email_id}: "
                            f"{attachment_result.get('error')}"
                        )
                    else:
                        print(
                            f"[EmailRepository] Recorded {attachment_result.get('attachments_added', 0)} "
                            f"attachment rows for email {email_id}"
                        )

                print(f"[EmailRepository] Attachments: {saved} downloaded, {skipped} skipped (already exist)")
        
        return db_result

    def _get_or_create_sender_account(
        self,
        from_domain: Optional[str],
        user_id: str,
        from_name: Optional[str] = None,
    ) -> Optional[str]:
        """Create or find an account based on sender domain."""

        account_name = from_name or from_domain

        if not account_name:
            raise ValueError("from_domain or from_name is required to create or find account")

        account_data = {"name": account_name}
        return self._create_or_find_account(account_data, user_id)

    def _get_or_create_sender_contact(
        self,
        from_email: Optional[str],
        from_name: Optional[str],
        account_id: Optional[str],
        user_id: str,
    ) -> Optional[str]:
        """Create or find a contact based on sender email/name."""
        if not from_email:
            raise ValueError("from_email is required to create or find contact")

        contact_data = {
            "name": (from_name or from_email),
            "email": from_email,
        }
        return self._create_or_find_contact(contact_data, account_id, user_id)

    def _has_fetch_expired(self, user_id: str) -> bool:
        """Check if email fetch cache has expired (> 30 seconds)."""
        latest_fetch = self.db_handler.get_latest_fetch_time(user_id)
        if latest_fetch:
            # Convert to UTC if not already
            if latest_fetch.tzinfo is None:
                latest_fetch = latest_fetch.replace(tzinfo=timezone.utc)
            
            time_since_fetch = (datetime.now(timezone.utc) - latest_fetch).total_seconds()
            print(f"[EmailRepository] Last fetch was {time_since_fetch:.1f} seconds ago")
            
            if time_since_fetch < 30:
                return False
        
        return True
    
    def _get_user_emails(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user emails from database and format for frontend."""
        db_emails = self.db_handler.get_emails_by_user(user_id, limit=limit)
        
        messages = []
        for email in db_emails:
            # Get labels for this email
            email_labels = self.db_handler.get_labels(email.get('id'))
            label_names = [label.get('label_name') for label in email_labels]
            email['labels'] = label_names
            
            # Get related opportunities
            email_id = email.get('id')
            opportunities = self._get_opportunities_for_email(email_id)
            email['opportunities'] = opportunities
            
            messages.append(email)

        return messages
    
    def _get_opportunities_for_email(self, email_id: str) -> List[Dict]:
        """Get opportunities related to this email."""
        try:
            supabase = get_supabase_service()
            response = supabase.table("opportunity").select(
                "id, stage, name"
            ).eq("source", "email").eq("source_reference_id", email_id).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"[EmailRepository] Error getting opportunities: {e}")
            return []
    
    @staticmethod
    def _get_gmail_paths() -> tuple:
        """Get Gmail credentials and token paths."""
        var_dir = Path(__file__).parent.parent.parent / "var"
        credentials_path = var_dir / "credentials.json"
        token_path = var_dir / "token.pickle"
        return credentials_path, token_path
    
    def _get_gmail_client(self, user_id: str = None) -> tuple:
        """Get initialized Gmail client with validation.
        
        Returns
        -------
        Tuple of (gmail_client, error_dict or None)
            If error_dict is not None, it's the error response to return
        """
        credentials_path, token_path = self._get_gmail_paths()
        
        if not credentials_path.exists():
            return None, {
                "status": "error",
                "error_code": "GMAIL_NOT_CONFIGURED",
                "message": "Gmail credentials not configured"
            }
        
        token_bytes = None
        token_saver = None

        if user_id:
            token_b64 = self._get_profile_token_b64(user_id)
            if token_b64:
                try:
                    token_bytes = base64.b64decode(token_b64.encode("utf-8"))
                    token_saver = lambda creds: self._save_profile_token(user_id, creds)
                except Exception:
                    token_bytes = None

        if not token_bytes and not token_path.exists():
            return None, {
                "status": "error",
                "error_code": "GMAIL_NOT_AUTHORIZED",
                "message": "Gmail not authorized. Please authorize first."
            }

        gmail_client = GmailClient(
            credentials_path=str(credentials_path),
            token_path=str(token_path),
            token_bytes=token_bytes,
            token_saver=token_saver,
        )
        return gmail_client, None

    def get_attachment_download(self, attachment_id: str, user_id: str = None):
        """Get attachment file for download.
        
        Parameters
        ----------
        attachment_id : str
            ID of the attachment
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Tuple of (status_code, headers_dict, file_content_bytes)
            For serving as HTTP response
        """
        try:
            supabase = get_supabase_service()
            
            # Get attachment from database
            response = supabase.table('email_attachment').select(
                'id, filename, mime_type, storage_path'
            ).eq('id', attachment_id).single().execute()
            
            if not response.data:
                return 404, {}, b''
            
            attachment = response.data
            storage_path = attachment.get('storage_path')
            filename = attachment.get('filename', 'attachment')
            mime_type = attachment.get('mime_type', 'application/octet-stream')
            
            if not storage_path or not Path(storage_path).exists():
                print(f"[EmailRepository] File not found: {storage_path}")
                return 404, {}, b''
            
            # Read file content
            with open(storage_path, 'rb') as f:
                file_content = f.read()
            
            # Prepare response headers
            if mime_type == 'application/pdf':
                disposition = f'inline; filename="{filename}"'
            else:
                disposition = f'attachment; filename="{filename}"'
            headers = {
                'Content-Type': mime_type,
                'Content-Disposition': disposition,
                'Content-Length': str(len(file_content))
            }
            
            return 200, headers, file_content
            
        except Exception as e:
            print(f"[EmailRepository] Error downloading attachment: {e}")
            return 500, {}, b''

    def delete_attachment(self, attachment_id: str, user_id: str = None) -> Dict:
        """Delete an email attachment (record + local file).

        Parameters
        ----------
        attachment_id : str
            ID of the attachment
        user_id : str, optional
            User ID for authorization
        """
        try:
            supabase = get_supabase_service()
            attachment_response = supabase.table('email_attachment').select(
                'id, email_id, storage_path, filename'
            ).eq('id', attachment_id).single().execute()

            if not attachment_response.data:
                return {"status": "error", "message": "Attachment not found"}

            attachment = attachment_response.data
            email_id = attachment.get('email_id')

            if user_id:
                email_response = supabase.table('email').select('id, user_id').eq('id', email_id).single().execute()
                if not email_response.data or email_response.data.get('user_id') != user_id:
                    return {"status": "error", "message": "Unauthorized"}

            storage_path = attachment.get('storage_path')
            if storage_path and Path(storage_path).exists():
                try:
                    Path(storage_path).unlink()
                except Exception as exc:
                    print(f"[EmailRepository] Failed to delete attachment file: {exc}")

            supabase.table('email_attachment').delete().eq('id', attachment_id).execute()
            return {"status": "ok", "deleted": attachment_id}
        except Exception as e:
            print(f"[EmailRepository] Error deleting attachment: {e}")
            return {"status": "error", "message": str(e)}

    def delete_email(self, email_id: str, user_id: str = None) -> Dict:
        """Delete an email and all related records (attachments, labels, opportunities).

        Parameters
        ----------
        email_id : str
            ID of the email to delete
        user_id : str, optional
            User ID for authorization

        Returns
        -------
        Dict
            Status of deletion
        """
        try:
            supabase = get_supabase_service()
            
            # Get email to verify ownership
            email_response = supabase.table('email').select('id, user_id').eq('id', email_id).single().execute()
            
            if not email_response.data:
                return {"status": "error", "message": "Email not found"}
            
            email = email_response.data
            if user_id and email.get('user_id') != user_id:
                return {"status": "error", "message": "Unauthorized"}
            
            # Get attachments to delete their files
            attachments_response = supabase.table('email_attachment').select('id, storage_path').eq('email_id', email_id).execute()
            attachments = attachments_response.data or []
            
            # Delete attachment files from disk
            for attachment in attachments:
                storage_path = attachment.get('storage_path')
                if storage_path and Path(storage_path).exists():
                    try:
                        Path(storage_path).unlink()
                        print(f"[EmailRepository] Deleted attachment file: {storage_path}")
                    except Exception as exc:
                        print(f"[EmailRepository] Failed to delete attachment file: {exc}")
            
            # Delete all related records (cascade deletes will handle attachments, labels)
            supabase.table('email').delete().eq('id', email_id).execute()
            
            print(f"[EmailRepository] Deleted email {email_id} and all related records")
            return {"status": "ok", "deleted": email_id}
            
        except Exception as e:
            print(f"[EmailRepository] Error deleting email: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def resync_email_from_gmail(self, email_id: str, provider_message_id: str, user_id: str) -> Dict:
        """Delete an email and re-fetch it from Gmail API with full processing.
        
        This method:
        1. Deletes the email and all related records (attachments, labels, etc)
        2. Fetches the email fresh from Gmail API
        3. Processes it the same way as fetch_emails.py (saves, classifies, extracts contacts)
        
        Parameters
        ----------
        email_id : str
            UUID of the email to resync
        provider_message_id : str
            Gmail message ID
        user_id : str
            User ID for authorization
        
        Returns
        -------
        Dict
            Status with result of resync operation
        """
        try:
            supabase = get_supabase_service()
            
            # Step 1: Verify ownership and get email details
            email_response = supabase.table('email').select(
                'id, user_id, provider_message_id'
            ).eq('id', email_id).single().execute()
            
            if not email_response.data or email_response.data.get('user_id') != user_id:
                return {"status": "error", "message": "Unauthorized or email not found"}
            
            # Step 2: Delete the email (this will cascade delete attachments, labels, etc)
            print(f"[EmailRepository] Deleting email {email_id} for resync...")
            supabase.table('email').delete().eq('id', email_id).execute()
            
            # Step 3: Fetch the email fresh from Gmail
            print(f"[EmailRepository] Fetching email {provider_message_id} from Gmail...")
            
            # Get Gmail client (same as fetch_from_gmail_and_save)
            gmail_client, error = self._get_gmail_client(user_id=user_id)
            if error:
                return error
            
            # Get the message from Gmail API (fetch full message with headers and body)
            service = gmail_client.get_service()
            full_message = service.users().messages().get(
                userId='me',
                id=provider_message_id,
                format='full'
            ).execute()
            
            if not full_message:
                return {"status": "error", "message": f"Email not found in Gmail: {provider_message_id}"}
            
            # Extract headers to reconstruct message in the format expected by _save_email_to_database
            headers = {h['name']: h['value'] for h in full_message.get('payload', {}).get('headers', [])}
            
            # Reconstruct message with necessary fields
            message = {
                'id': full_message.get('id'),
                'threadId': full_message.get('threadId'),
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'cc': headers.get('Cc', ''),
                'date': headers.get('Date', ''),
                'snippet': full_message.get('snippet', ''),
                'labelIds': full_message.get('labelIds', []),
            }
            
            # Add headers to message for auth parsing
            message['payload'] = full_message.get('payload', {})
            
            if not message.get('date'):
                return {"status": "error", "message": f"Email missing date header: {provider_message_id}"}
            
            # Step 4: Save the email to database (same as fetch workflow)
            print(f"[EmailRepository] Saving email to database...")
            save_result = self._save_email_to_database(gmail_client, message, user_id)
            
            if not save_result.get('success'):
                return {
                    "status": "error",
                    "message": f"Failed to save email: {save_result.get('error', 'Unknown error')}"
                }
            
            new_email_id = save_result.get('email_id')
            
            # Step 5: Classify the email
            print(f"[EmailRepository] Classifying email...")
            classify_result = self.classify_unclassified_emails(user_id=user_id, limit=1)
            
            return {
                "status": "ok",
                "email_id": new_email_id,
                "message": "Email successfully resynced",
                "classified": classify_result.get("classified", 0),
                "rfq_processed": classify_result.get("rfq_processed", 0),
                "opportunities_created": classify_result.get("opportunities_created", 0)
            }
            
        except Exception as e:
            print(f"[EmailRepository] Error resyncing email: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def extract_contact_from_email_body(self, email_id: str = None, email_body: str = None, user_id: str = None) -> Dict:
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
        if not email_body:
            return {
                "status": "error",
                "message": "Email body is required"
            }
        
        try:
            from src.infrastructure.llm_factory import LLMClientFactory
            import re
            from html.parser import HTMLParser
            
            # Strip HTML tags and decode entities
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.strict = False
                    self.convert_charrefs = True
                    self.text = []
                    self.skip_tags = set()
                
                def handle_starttag(self, tag, attrs):
                    # Skip style, script, and head content
                    if tag in ('style', 'script', 'head'):
                        self.skip_tags.add(tag)
                
                def handle_endtag(self, tag):
                    self.skip_tags.discard(tag)
                
                def handle_data(self, d):
                    # Only append data if not inside skip tags
                    if not self.skip_tags:
                        self.text.append(d)
                
                def get_data(self):
                    return ''.join(self.text)
            
            # Try to strip HTML
            stripper = MLStripper()
            try:
                stripper.feed(email_body)
                text_body = stripper.get_data()
            except Exception:
                text_body = email_body
            
            # Clean up whitespace
            text_body = re.sub(r'\s+', ' ', text_body).strip()
            
            # Truncate to reasonable size (around 3000 characters ~750 tokens)
            # to fit within the 4096 token context window
            if len(text_body) > 3000:
                text_body = text_body[:3000] + "..."
            
            print(f"[EmailRepository] Text body for LLM (length={len(text_body)}): {text_body[:500]}...", flush=True)
            
            # Initialize LLM client
            factory = LLMClientFactory()
            llm_client = factory.create_client()
            
            # Create extraction prompt
            extraction_prompt = f"""Extract contact and account/company information from the following email:

EMAIL:
{text_body}

Please extract and return the following information in JSON format:
{{
  "contact": {{
    "name": "person's full name",
    "email": "person's email address",
    "phone": "phone number if available",
    "title": "job title if available",
    "address": "street address if available",
    "city": "city/town if available",
    "zip_code": "postal/zip code if available",
    "country": "country if available"
  }},
  "account": {{
    "name": "company/account name",
    "industry": "industry if mentioned",
    "address": "company address if available",
    "city": "city/town if available",
    "zip_code": "postal/zip code if available",
    "country": "country/location if mentioned",
    "phone": "company phone number if available",
    "website": "company website if available"
  }}
}}

Return ONLY valid JSON, no additional text."""
            
            # Call LLM using ask_json
            extracted_data = llm_client.ask_json(
                system_prompt="You are an expert at extracting business contact and company information from emails. Return only valid JSON.",
                user_content=extraction_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            import sys
            print(f"[EmailRepository] LLM raw response: {extracted_data}", flush=True)
            sys.stdout.flush()
            
            # Ensure we have a dict response
            if not isinstance(extracted_data, dict):
                # Try to parse if it's a string
                import json as json_module
                try:
                    extracted_data = json_module.loads(str(extracted_data))
                except (json_module.JSONDecodeError, ValueError):
                    return {
                        "status": "error",
                        "message": "Could not parse LLM response as JSON"
                    }
            
            # Extract account and contact data
            account_data = extracted_data.get("account", {})
            contact_data = extracted_data.get("contact", {})
            
            print(f"[EmailRepository] Extracted data - Account: {account_data}")
            print(f"[EmailRepository] Extracted data - Contact: {contact_data}")
            
            # Create or find account
            account_id = None
            if account_data.get("name"):
                account_id = self._create_or_find_account(account_data, user_id)
            
            # Create or find contact
            contact_id = None
            if contact_data.get("email") or contact_data.get("name"):
                contact_id = self._create_or_find_contact(contact_data, account_id, user_id)

            # Link extracted contact/account to the email
            if email_id and (contact_id or account_id):
                update_data = {}
                if contact_id:
                    update_data["contact_id"] = contact_id
                if account_id:
                    update_data["account_id"] = account_id

                try:
                    supabase = get_supabase_service()
                    supabase.table("email").update(update_data).eq("id", email_id).execute()
                except Exception as link_error:
                    if "contact_id" in str(link_error) or "account_id" in str(link_error):
                        print(
                            "[EmailRepository] Note: Email table columns not yet in schema cache. "
                            "Contact/account created but email not linked."
                        )
                    else:
                        print(f"[EmailRepository] Warning: Could not link email to contact/account: {link_error}")
            
            return {
                "status": "ok",
                "contact": {
                    "id": contact_id,
                    **contact_data
                },
                "account": {
                    "id": account_id,
                    **account_data
                },
                "message": "Contact and account information extracted and saved successfully"
            }
            
        except Exception as e:
            print(f"[EmailRepository] Error extracting contact: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error extracting contact: {str(e)}"
            }

    def _create_or_find_account(self, account_data: Dict, user_id: str = None) -> str:
        """Create or find account by name.
        
        Parameters
        ----------
        account_data : Dict
            Account information with name, industry, address, etc.
        user_id : str, optional
            User ID for database operations
        
        Returns
        -------
        str
            Account ID
        """
        try:
            supabase = get_supabase_service()
            account_name = account_data.get("name", "").strip()
            
            if not account_name:
                raise Exception("Account name is required") 
            
            print(f"[EmailRepository] Looking for existing account: {account_name}")
            
            # Try to find existing account by name
            response = supabase.table('account').select('id').ilike('name', f'{account_name}').limit(1).execute()
            
            if response.data and len(response.data) > 0:
                print(f"[EmailRepository] Found existing account: {response.data[0]['id']}")
                return response.data[0]['id']
            
            print(f"[EmailRepository] Creating new account with user_id: {user_id}")
            
            # Create new account.
            # Some environments have a reduced account schema: if optional columns are
            # unknown to PostgREST, retry with minimal payload.
            new_account = {
                "name": account_name,
                "industry": account_data.get("industry"),
                "address_line1": account_data.get("address"),
                "city": account_data.get("city"),
                "postal_code": account_data.get("zip_code"),
                "country_code": account_data.get("country", "").upper()[:2] if account_data.get("country") else None,
                "phone": account_data.get("phone"),
                "website": account_data.get("website")
            }

            try:
                response = supabase.table('account').insert(new_account).execute()
            except Exception as insert_error:
                error_text = str(insert_error)
                if "schema cache" in error_text and "column" in error_text:
                    print("[EmailRepository] Account schema mismatch; retrying insert with name only")
                    response = supabase.table('account').insert({"name": account_name}).execute()
                else:
                    raise
            
            if response.data and len(response.data) > 0:
                print(f"[EmailRepository] Created account: {response.data[0]['id']}")
                return response.data[0]['id']
            
            print(f"[EmailRepository] Failed to create account, no data returned: {response}")
            return None
            
        
        except Exception as e:
            print(f"[EmailRepository] Error creating/finding account: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_or_find_contact(self, contact_data: Dict, account_id: str = None, user_id: str = None) -> str:
        """Create or find contact by email.
        
        Parameters
        ----------
        contact_data : Dict
            Contact information with name, email, phone, title, etc.
        account_id : str, optional
            Account ID to link contact to
        user_id : str, optional
            User ID for database operations
        
        Returns
        -------
        str
            Contact ID
        """
        try:
            supabase = get_supabase_service()
            contact_email = contact_data.get("email")
            if not contact_email:
                raise Exception("Contact email is required")

            contact_email = contact_email.strip().lower()
            if not account_id:
                raise ValueError("account_id is required to create or find contact")

            print(f"[EmailRepository] Looking for existing contact with email: {contact_email}")
            response = (
                supabase.table('contact')
                .select('id')
                .eq('email', contact_email)
                .eq('account_id', account_id)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                print(f"[EmailRepository] Found existing contact: {response.data[0]['id']}")
                return response.data[0]['id']

            print(f"[EmailRepository] Creating new contact for account: {account_id}")
            new_contact = {
                "name": contact_data.get("name"),
                "email": contact_email,
                "phone": contact_data.get("phone"),
                "role_title": contact_data.get("title"),
                "account_id": account_id,
            }

            response = supabase.table('contact').insert(new_contact).execute()
            if response.data and len(response.data) > 0:
                print(f"[EmailRepository] Created contact: {response.data[0]['id']}")
                return response.data[0]['id']

            print(f"[EmailRepository] Failed to create contact, no data returned: {response}")
            raise Exception("Failed to create contact, no data returned")

        except Exception as e:
            raise e


class EmailHTMLParser(HTMLParser):
    """Parse and extract plain text from HTML emails, skipping styles and scripts."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_content = False
        self.skip_tags = {'style', 'script', 'head'}
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip_content = True
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_content = False
    
    def handle_data(self, data):
        if not self.skip_content:
            self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)

