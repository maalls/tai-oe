"""Document-related request handlers."""

from pathlib import Path
from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text, extract_rfp_from_text
from src.service.opportunity.document_content_service import DocumentContentService
from src.service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


class DocumentHandlers:
    """Handle document-related API requests."""

    def __init__(
        self,
        supabase=None,
        storage_dir_resolver: Callable = None,
        storage_path_resolver: Callable = None,
        clean_email_body: Callable = None,
        enrich_rfp: Callable = None,
    ):
        self.supabase = supabase or get_supabase_service()
        self.storage_dir_resolver = storage_dir_resolver
        self.storage_path_resolver = storage_path_resolver
        self.clean_email_body = clean_email_body
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
        return self.document_content_service.update_document_content(
            document_id=document_id,
            content=content,
        )

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_rfp_extraction_service.extract_from_document(document_id=document_id)

    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete a quote document and its related data."""
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
                return {"status": "error", "message": "Quote document not found"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "Document is not a quote"}

            self._delete_storage_file(storage_type="quote", storage_key=document.get("storage_key"))

            delete_resp = self.supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete quote: {delete_resp.error}"}

            return {"status": "ok", "message": "Quote deleted successfully"}

        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Error deleting quote document {document_id}: {e}")
            return {
                "status": "error",
                "message": f"Error deleting quote: {str(e)}",
            }

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete any document and its related data."""
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

        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Error deleting document {document_id}: {e}")
            return {
                "status": "error",
                "message": f"Error deleting document: {str(e)}",
            }

    def _delete_storage_file(self, storage_type: str, storage_key: str) -> None:
        if not storage_key:
            return

        try:
            if self.storage_path_resolver is not None:
                storage_path = self.storage_path_resolver(storage_type, storage_key)
                if storage_path.exists():
                    storage_path.unlink()
                    return

            legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            legacy_path = legacy_assets_dir / storage_key
            if legacy_path.exists():
                legacy_path.unlink()
        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Warning: Could not delete file {storage_key}: {e}")
