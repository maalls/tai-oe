"""Service for document content update workflows."""

from datetime import datetime
from typing import Callable, Dict

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler


class DocumentContentService:
    """Update document storage content and related opportunity metadata."""

    def __init__(
        self,
        supabase=None,
        db_handler: DatabaseHandler | None = None,
        storage_dir_resolver: Callable[[str], object] = None,
        now_provider: Callable[[], datetime] = None,
    ):
        if storage_dir_resolver is None:
            raise ValueError("DocumentContentService requires storage_dir_resolver")
        self.supabase = supabase
        self.db_handler = db_handler
        self.storage_dir_resolver = storage_dir_resolver
        self.now_provider = now_provider or datetime.utcnow

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def _get_document(self, document_id: str) -> Dict | None:
        rows = self._get_db_handler().execute_dict_query(
            """
            SELECT id, storage_key, type, opportunity_id
            FROM document
            WHERE id = %s
            LIMIT 1
            """,
            (document_id,),
        )
        return rows[0] if rows else None

    def _touch_opportunity(self, opportunity_id: str) -> None:
        updated_at = self.now_provider().isoformat()
        self._get_db_handler().execute_update(
            "UPDATE opportunity SET updated_at = %s WHERE id = %s",
            (updated_at, opportunity_id),
        )

    def update_document_content(self, document_id: str, content: str) -> Dict:
        try:
            document = self._get_document(document_id)
            if not document:
                return {"status": "error", "message": "Document not found"}

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
                    self._touch_opportunity(opportunity_id)
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
