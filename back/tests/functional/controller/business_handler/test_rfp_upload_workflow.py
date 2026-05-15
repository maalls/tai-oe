"""
Functional test: RFP Upload Workflow
Tests the complete flow: upload PDF → parse RFP → extract data → save to DB

Structure: Tests are organized to mirror source code structure
- test_rfp_upload_workflow.py tests the full integration
- Organized under tests/functional/ alongside tests/integration/, tests/unit/
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

# Setup path to import backend modules
# File is under tests/functional/controller/business_handler/, so back/ is parents[4].
test_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(test_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(test_root / ".env")

from src.api.business.handler import BusinessHandlers
from src.infrastructure.clients.database import get_db_handler


class TestRFPUploadFunctional:
    """Test complete RFP upload workflow with real database."""

    def setup_method(self):
        self.test_assets_dir = Path(__file__).resolve().parents[3] / "assets" / "rfp"
        self.db_handler = get_db_handler()
        self.business_handlers = BusinessHandlers()

    def test_upload_rfp_pdf_with_multipart(self):
        """
        Test uploading an RFP PDF file via multipart form data.
        
        Validates:
        - File is uploaded successfully
        - Form data is parsed correctly
        - Response contains uploaded file info
        """
        print("\n" + "=" * 60)
        print("TEST: Upload RFP PDF with multipart form data")
        print("=" * 60)

        pdf_file = self.test_assets_dir / "rfp.pdf"
        if not pdf_file.exists():
            raise FileNotFoundError(f"Missing required test asset: {pdf_file}")

        print(f"\n📄 Using test file: {pdf_file.name}")

        # Read PDF binary
        with open(pdf_file, "rb") as f:
            pdf_content = f.read()

        print(f"   File size: {len(pdf_content)} bytes")

        # Build multipart form data manually
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = self._build_multipart_body(
            boundary=boundary,
            fields={
                "message": "Test RFP upload",
                "title": "Test Opportunity",
            },
            files={
                "rfp": {
                    "filename": pdf_file.name,
                    "content": pdf_content,
                    "content_type": "application/pdf",
                },
            },
        )

        content_type = f"multipart/form-data; boundary={boundary}"

        # Keep this functional test deterministic by stubbing LLM extraction.
        fake_rfp_data = {
            "products": [
                {
                    "manufacturer": "TEST-MFG",
                    "sku": "TEST-001",
                    "description": "Functional test product",
                    "quantity": 1,
                }
            ]
        }
        with patch("src.api.rfq.handler.extract_rfp_from_text", return_value=fake_rfp_data):
            result = self.business_handlers.handle_rfp_upload(body=body, content_type=content_type)

        print(f"\n✓ Response status: {result.get('status')}")
        print(f"✓ Files received: {result.get('total_files')}")
        print(f"✓ Files list: {result.get('files')}")

        assert result.get("status") == "ok", f"Expected status 'ok', got {result.get('status')}"
        assert result.get("total_files") == 1, f"Expected 1 file, got {result.get('total_files')}"
        assert pdf_file.name in result.get("files", []), f"PDF file not in response"

    def test_create_opportunity_from_rfp_text(self):
        """
        Test creating an opportunity from extracted RFP text data.
        
        Validates:
        - Opportunity can be created via API
        - Document type can be set correctly
        """
        print("\n" + "=" * 60)
        print("TEST: Create Opportunity from RFP text data")
        print("=" * 60)

        from src.infrastructure.clients.supabase import get_supabase_service
        supabase = get_supabase_service()

        opportunity = self._create_test_opportunity(supabase, "Test RFP Opportunity")
        assert opportunity.get("id"), "Created opportunity has no id"
        assert opportunity.get("name") == "Test RFP Opportunity", "Opportunity name mismatch"

    def test_attachment_enum_exists(self):
        """
        Test that ATTACHMENT enum value exists in database.
        
        Validates:
        - Database schema includes ATTACHMENT in document_type enum
        - Can insert documents with type ATTACHMENT
        """
        print("\n" + "=" * 60)
        print("TEST: ATTACHMENT enum exists in database")
        print("=" * 60)

        from src.infrastructure.clients.supabase import get_supabase_service
        supabase = get_supabase_service()

        opportunity = self._create_test_opportunity(supabase, "Test enum ATTACHMENT")
        opportunity_id = opportunity["id"]

        doc_response = supabase.table("document").insert(
            {
                "opportunity_id": opportunity_id,
                "type": "ATTACHMENT",
                "title": "Enum probe attachment",
                "channel": "OTHER",
                "status": "DRAFT",
            }
        ).execute()
        assert doc_response.data and len(doc_response.data) > 0, "ATTACHMENT enum value is not accepted"

    def test_attachment_document_insert(self):
        """
        Test inserting a document with ATTACHMENT type.
        
        Validates:
        - Can create document with type ATTACHMENT
        - Document persists in database
        """
        print("\n" + "=" * 60)
        print("TEST: Insert document with ATTACHMENT type")
        print("=" * 60)

        from src.infrastructure.clients.supabase import get_supabase_service
        supabase = get_supabase_service()

        opportunity = self._create_test_opportunity(supabase, "Test Opportunity for Attachment")
        opportunity_id = opportunity["id"]

        doc_response = supabase.table("document").insert(
            {
                "opportunity_id": opportunity_id,
                "type": "ATTACHMENT",
                "title": "Test Attachment",
                "channel": "OTHER",
                "status": "DRAFT",
            }
        ).execute()

        assert doc_response.data and len(doc_response.data) > 0, "Failed to insert ATTACHMENT document"
        doc = doc_response.data[0]
        assert doc.get("type") == "ATTACHMENT", "Document type mismatch after insert"

    # Helper methods

    def _build_multipart_body(
        self, boundary: str, fields: Dict[str, str], files: Dict[str, Dict[str, Any]]
    ) -> bytes:
        """Build raw multipart/form-data body."""
        body_parts = []

        # Add text fields
        for name, value in fields.items():
            body_parts.append(f"--{boundary}".encode())
            body_parts.append(
                f'Content-Disposition: form-data; name="{name}"'.encode()
            )
            body_parts.append(b"")
            body_parts.append(str(value).encode("utf-8"))

        # Add files
        for field_name, file_info in files.items():
            body_parts.append(f"--{boundary}".encode())
            filename = file_info.get("filename", "file.bin")
            content_type = file_info.get("content_type", "application/octet-stream")
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode()
            )
            body_parts.append(f"Content-Type: {content_type}".encode())
            body_parts.append(b"")
            body_parts.append(file_info["content"])

        # End boundary
        body_parts.append(f"--{boundary}--".encode())
        body_parts.append(b"")

        return b"\r\n".join(body_parts)

    def _ensure_test_account_id(self, supabase) -> str:
        """Get or create a reusable account id for opportunity inserts."""
        account_name = "Functional Test Account"
        account_resp = supabase.table("account").select("id").eq("name", account_name).limit(1).execute()
        if account_resp.data:
            return account_resp.data[0]["id"]

        created = supabase.table("account").insert({"name": account_name}).execute()
        assert created.data and len(created.data) > 0, "Failed to create test account"
        return created.data[0]["id"]

    def _create_test_opportunity(self, supabase, name: str) -> Dict[str, Any]:
        """Insert an opportunity using the current schema (no owner_user_id required)."""
        account_id = self._ensure_test_account_id(supabase)
        opp_resp = supabase.table("opportunity").insert(
            {
                "account_id": account_id,
                "name": name,
                "stage": "NEW_LEAD",
                "status": "OPEN",
                "source": "manual",
            }
        ).execute()
        assert opp_resp.data and len(opp_resp.data) > 0, "Failed to create opportunity"
        return opp_resp.data[0]

