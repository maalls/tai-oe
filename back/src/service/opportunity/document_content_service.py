"""Service for document content update workflows."""

from datetime import datetime
from typing import Callable, Dict


class DocumentContentService:
    """Update document storage content and related opportunity metadata."""

    def __init__(
        self,
        supabase,
        storage_dir_resolver: Callable[[str], object],
        now_provider: Callable[[], datetime] = None,
    ):
        self.supabase = supabase
        self.storage_dir_resolver = storage_dir_resolver
        self.now_provider = now_provider or datetime.utcnow

    def update_document_content(self, document_id: str, content: str) -> Dict:
        try:
            doc_result = (
                self.supabase
                .table("document")
                .select("id, storage_key, type, opportunity_id")
                .eq("id", document_id)
                .single()
                .execute()
            )
            if not doc_result.data:
                return {"status": "error", "message": "Document not found"}

            document = doc_result.data
            storage_key = document.get("storage_key")
            opportunity_id = document.get("opportunity_id")

            if not storage_key:
                return {"status": "error", "message": "Document has no storage file"}

            storage_dir = self.storage_dir_resolver("rfp_upload")
            file_path = storage_dir / storage_key

            if not file_path.exists():
                return {"status": "error", "message": f"Document file not found: {storage_key}"}

            file_path.write_text(content, encoding="utf-8")
            print(f"[DocumentContentService] Updated document content: {document_id} -> {storage_key}")

            if opportunity_id:
                try:
                    self.supabase.table("opportunity").update(
                        {"updated_at": self.now_provider().isoformat()}
                    ).eq("id", opportunity_id).execute()
                    print(f"[DocumentContentService] Updated opportunity timestamp: {opportunity_id}")
                except Exception as exc:
                    print(f"[DocumentContentService] Warning: Could not update opportunity timestamp: {exc}")

            return {
                "status": "ok",
                "message": "Document content updated successfully",
                "document_id": document_id,
            }
        except Exception as exc:
            print(f"[DocumentContentService] Error updating document content: {exc}")
            return {
                "status": "error",
                "message": f"Failed to update document content: {str(exc)}",
            }
