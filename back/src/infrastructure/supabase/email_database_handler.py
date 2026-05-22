"""Email database persistence helpers extracted from EmailRepository."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
from typing import Dict, List, Optional

from src.infrastructure.clients.supabase import get_supabase_service


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


class EmailDatabaseHandler:
    """Handle email storage in Supabase database."""

    def __init__(self):
        self.supabase = get_supabase_service()

    
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


