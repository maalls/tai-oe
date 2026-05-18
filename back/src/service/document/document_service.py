"""Document service for FastAPI transport."""

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict
import time
import uuid

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text, extract_rfp_from_text
from src.lib.storage_paths import get_storage_dir, get_storage_path
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository
from src.service.opportunity.document_content_service import DocumentContentService
from src.service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


class DocumentService:
    """Handle document extraction/update/delete and chat attachment upload."""

    def __init__(
        self,
        supabase=None,
        storage_dir_resolver: Callable = None,
        storage_path_resolver: Callable = None,
        clean_email_body: Callable = None,
        enrich_rfp: Callable = None,
    ):
        self.supabase = supabase or get_supabase_service()
        self.storage_dir_resolver = storage_dir_resolver or get_storage_dir
        self.storage_path_resolver = storage_path_resolver or get_storage_path
        self.clean_email_body = clean_email_body or EmailRepository._clean_email_body

        if enrich_rfp is None:
            opportunity_repository = OpportunityRepository()
            self.enrich_rfp = (
                lambda message_clean, pre_extracted_data: opportunity_repository._extract_and_enrich_rfp_data(
                    message_clean,
                    pre_extracted_data=pre_extracted_data,
                )
            )
        else:
            self.enrich_rfp = enrich_rfp

        self._document_content_service = None
        self._document_rfp_extraction_service = None

    @property
    def document_content_service(self) -> DocumentContentService:
        if self._document_content_service is None:
            self._document_content_service = DocumentContentService(
                supabase=self.supabase,
                storage_dir_resolver=self.storage_dir_resolver,
            )
        return self._document_content_service

    @property
    def document_rfp_extraction_service(self) -> DocumentRfpExtractionService:
        if self._document_rfp_extraction_service is None:
            self._document_rfp_extraction_service = DocumentRfpExtractionService(
                supabase=self.supabase,
                storage_path_resolver=self.storage_path_resolver,
                clean_email_body=self.clean_email_body,
                extract_rfp=extract_rfp_from_text,
                extract_company=extract_company_from_text,
                enrich_rfp=self.enrich_rfp,
            )
        return self._document_rfp_extraction_service

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_content_service.update_document_content(document_id=document_id, content=content)

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_rfp_extraction_service.extract_from_document(document_id=document_id)

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        _ = user_id
        try:
            doc_resp = (
                self.supabase.table("document")
                .select("id, type, storage_key, opportunity_id")
                .eq("id", document_id)
                .maybe_single()
                .execute()
            )
            document = doc_resp.data if doc_resp and doc_resp.data else None

            if not document:
                return {"status": "error", "message": "Document not found"}

            doc_type = str(document.get("type") or "").lower()
            storage_type = "quote" if doc_type == "quote" else "invoice" if doc_type == "invoice" else "rfp_upload"
            self._delete_storage_file(storage_type=storage_type, storage_key=document.get("storage_key"))

            delete_resp = self.supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete document: {delete_resp.error}"}

            return {
                "status": "ok",
                "message": f"{document.get('type', 'Document')} deleted successfully",
            }

        except Exception as exc:
            print(f"[DocumentService] Error deleting document {document_id}: {exc}")
            return {
                "status": "error",
                "message": f"Error deleting document: {str(exc)}",
            }

    def _delete_storage_file(self, storage_type: str, storage_key: str) -> None:
        if not storage_key:
            return

        try:
            storage_path = self.storage_path_resolver(storage_type, storage_key)
            if storage_path.exists():
                storage_path.unlink()
                return

            legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            legacy_path = legacy_assets_dir / storage_key
            if legacy_path.exists():
                legacy_path.unlink()
        except Exception as exc:
            print(f"[DocumentService] Warning: Could not delete file {storage_key}: {exc}")

    def handle_chat_attachment_upload(
        self,
        filename: str,
        file_content: bytes,
        mime_type: str,
        file_size: int,
        user_id: str,
        opportunity_id: str,
    ) -> Dict:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        if not opportunity_id:
            return {"status": "error", "message": "Missing opportunity_id"}
        if not filename or not file_content:
            return {"status": "error", "message": "No file provided"}

        try:
            unique_name = f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"
            storage_key = unique_name

            storage_dir = self.storage_dir_resolver("attachment")
            storage_dir.mkdir(parents=True, exist_ok=True)
            (storage_dir / storage_key).write_bytes(file_content)

            doc_data = {
                "opportunity_id": opportunity_id,
                "type": "ATTACHMENT",
                "status": "RECEIVED",
                "title": f"Chat Attachment: {filename}",
                "currency": "EUR",
                "channel": "OTHER",
                "storage_key": storage_key,
                "created_by": user_id,
            }

            doc_result = self.supabase.table("document").insert(doc_data).execute()
            if not doc_result.data:
                return {"status": "error", "message": "Failed to create document"}

            document_id = doc_result.data[0]["id"]

            try:
                self.supabase.table("opportunity").update({"updated_at": datetime.now().isoformat()}).eq(
                    "id", opportunity_id
                ).execute()
            except Exception as exc:
                print(f"[DocumentService] Warning: failed to touch opportunity {opportunity_id}: {exc}")

            return {
                "status": "ok",
                "document_id": document_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": file_size,
                "storage_key": storage_key,
            }
        except Exception as exc:
            print(f"[DocumentService] Error uploading chat attachment: {exc}")
            return {"status": "error", "message": f"Upload failed: {str(exc)}"}
