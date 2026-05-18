"""RFQ service for FastAPI transport."""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict

from src.infrastructure.factory import ServiceFactory
from src.lib.extractors.text_reader import extract_rfp_from_text
from src.repository.email_repository import EmailRepository


class RfqService:
    """Provide RFQ draft generation and RFP upload parsing for FastAPI."""

    def __init__(self, service_factory: ServiceFactory = None, email_repository: EmailRepository = None):
        self.service_factory = service_factory or ServiceFactory()
        self.email_repository = email_repository or EmailRepository()

    def _load_email_content(self, message_id: str) -> str:
        email_service = self.service_factory.create_email_service()
        email = email_service.get_email(message_id)
        if email.body:
            return email.body

        legacy_email = self.email_repository.db_handler.get_email(message_id)
        if legacy_email:
            return legacy_email.get("body_full") or legacy_email.get("body_preview") or ""

        return ""

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        _ = user_id
        try:
            content = text or ""
            if not content and message_id:
                try:
                    content = self._load_email_content(message_id)
                except Exception as exc:
                    print(f"[RfqService] Warning: could not load email body for RFQ generation: {exc}")

            if not content:
                return {"status": "error", "message": "No text provided and unable to load email body"}

            draft = extract_rfp_from_text(content, timeout_seconds=300)
            return {"status": "ok", "rfq_id": str(uuid.uuid4()), "type": "RFQ", "draft": draft}
        except Exception as exc:
            print(f"[RfqService] Error generating RFQ: {exc}")
            return {"status": "error", "message": f"Error generating RFQ: {str(exc)}"}

    def handle_rfp_upload(self, body: bytes, content_type: str) -> Dict:
        try:
            form_data, error = self.get_form(body, content_type)
            if error:
                return error

            text_fields = {
                key: value for key, value in form_data.items() if not isinstance(value, dict) or "filename" not in value
            }
            files = {
                key: value for key, value in form_data.items() if isinstance(value, dict) and "filename" in value
            }

            message_text = text_fields.get("message", "") or ""
            cache_flag = str(text_fields.get("cache", "false")).lower() in ("1", "true", "yes", "on")

            cache_hit = False
            rfp_data = None
            cache_dir = Path("var/storage/rfp_cache")
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

            key = hashlib.sha256(message_text.encode("utf-8")).hexdigest()
            cache_file = cache_dir / f"{key}.json"

            if cache_flag and cache_file.exists():
                try:
                    rfp_data = json.loads(cache_file.read_text(encoding="utf-8"))
                    cache_hit = True
                except Exception as exc:
                    print(f"[RfqService] Cache read error: {exc}")

            if rfp_data is None:
                rfp_data = extract_rfp_from_text(message_text)
                for product in rfp_data.get("products", []) or []:
                    if "part_number" in product and "sku" not in product:
                        product["sku"] = product.pop("part_number")
                for product in rfp_data.get("products", []) or []:
                    product["price_found"] = bool(product.get("price"))
                    product["price"] = product.get("price")

                if cache_flag:
                    try:
                        cache_file.write_text(json.dumps(rfp_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    except Exception as exc:
                        print(f"[RfqService] Cache write error: {exc}")

            return {
                "status": "ok",
                "message": "RFP received successfully",
                "text_fields": list(text_fields.keys()),
                "files": [f.get("filename") for f in files.values() if isinstance(f, dict)],
                "total_files": len(files),
                "extracted_rfp": rfp_data,
                "cache": "hit" if cache_hit else ("miss" if cache_flag else "off"),
            }
        except Exception as exc:
            print(f"[RfqService] Error processing RFP: {exc}")
            return {"status": "error", "message": f"Error processing RFP: {str(exc)}"}

    def get_form(self, body: bytes, content_type: str):
        boundary = self._extract_boundary(content_type)
        if not boundary:
            return None, {"status": "error", "message": "Invalid content type"}
        return self._parse_multipart(body, boundary), None

    @staticmethod
    def _extract_boundary(content_type: str):
        if "boundary=" not in content_type:
            return None
        boundary = content_type.split("boundary=")[1]
        return boundary.strip('"\'')

    @staticmethod
    def _parse_multipart(body: bytes, boundary: str) -> Dict:
        form_data = {}
        parts = body.split(f"--{boundary}".encode())
        for part in parts[1:-1]:
            if not part.strip():
                continue
            try:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    header_end = part.find(b"\n\n")
                    if header_end == -1:
                        continue
                    content_start = header_end + 2
                else:
                    content_start = header_end + 4

                headers = part[:header_end].decode("utf-8", errors="ignore")
                content = part[content_start:]
                if content.endswith(b"\r\n"):
                    content = content[:-2]
                elif content.endswith(b"\n"):
                    content = content[:-1]

                if "Content-Disposition" in headers:
                    disp_line = [h for h in headers.split("\n") if "Content-Disposition" in h][0]
                    if 'name="' in disp_line:
                        name_start = disp_line.find('name="') + 6
                        name_end = disp_line.find('"', name_start)
                        name = disp_line[name_start:name_end]
                        if "filename=" in disp_line:
                            filename_start = disp_line.find('filename="') + 10
                            filename_end = disp_line.find('"', filename_start)
                            filename = disp_line[filename_start:filename_end]
                            part_content_type = "application/octet-stream"
                            for header_line in headers.split("\n"):
                                if "Content-Type:" in header_line:
                                    part_content_type = header_line.split("Content-Type:")[1].strip()
                            form_data[name] = {
                                "filename": filename,
                                "content": content,
                                "content_type": part_content_type,
                                "size": len(content),
                            }
                        else:
                            form_data[name] = content.decode("utf-8", errors="ignore")
            except Exception as exc:
                print(f"[RfqService] Error parsing part: {exc}")
                continue
        return form_data
