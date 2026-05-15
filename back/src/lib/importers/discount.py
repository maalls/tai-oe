"""
Discount Importer for updating family discount entries from PDF files using LLM extraction.
"""

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from src.infrastructure.clients.llm import extract_json_from_text


class DiscountImporter:
    """Imports and updates family discount information from PDF files."""

    DISCOUNT_SYSTEM_PROMPT = (
        "You extract family discount rows from supplier documents. "
        "Return only valid JSON and no extra text."
    )

    DISCOUNT_EXTRACTION_RULES = (
        "Extract the existing family discount table from the document. "
        "Each row is one family. Ignore everything outside the table.\n"
        "For each row, return these exact fields:\n"
        "- family_code (shortest code when multiple codes appear)\n"
        "- description\n"
        "- quantity\n"
        "- discount\n\n"
        "Rules:\n"
        "- Output strictly this JSON shape: {\"families\": [ ... ]}.\n"
        "- Keep family_code/description as strings.\n"
        "- quantity and discount should be numeric when possible.\n"
        "- discount ('remise' in french) is a percentage value between 0 and 100.\n"
        "- If a field is missing in a row, use null.\n"
        "- Do not invent rows."
    )

    def __init__(self, supabase_client, llm_client):
        self.supabase_client = supabase_client
        self.llm_client = llm_client
        self.brand = None
        self.pdf_path = None
        self.pdf_text = None

    def setBrand(self, brand_name: str) -> dict:
        """Set current brand context by looking up the brand entry in database."""
        normalized_name = (brand_name or "").strip()
        if not normalized_name:
            raise ValueError("Brand name is required")

        response = (
            self.supabase_client.table("brand")
            .select("id,name,marque,vendor_id")
            .eq("name", normalized_name)
            .execute()
        )

        if getattr(response, "error", None):
            raise RuntimeError(f"Failed to query brand '{normalized_name}': {response.error}")

        if not response.data:
            raise ValueError(f"Brand not found: '{normalized_name}'")

        if len(response.data) > 1:
            raise ValueError(f"Multiple brands found for name '{normalized_name}'")

        brand = response.data[0]
        if not brand.get("id"):
            raise RuntimeError(f"Brand '{normalized_name}' returned without id")

        self.brand = brand
        return brand

    def load_pdf(self, pdf_path: str | Path) -> str:
        """Load PDF content as plain text for downstream extraction."""
        path = Path(pdf_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {path}")

        reader = PdfReader(str(path))
        page_texts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page_texts).strip()
        if not text:
            raise ValueError(f"No extractable text found in PDF: {path}")

        self.pdf_path = path
        self.pdf_text = text
        return text

    def parseDiscounts(self, source_text: str | None = None) -> list[dict[str, Any]]:
        """Extract family discount rows from PDF text using the LLM."""
        text = (source_text or self.pdf_text or "").strip()
        if not text:
            raise ValueError("No text available to parse. Call load_pdf() first or pass source_text.")

        user_content = f"{self.DISCOUNT_EXTRACTION_RULES}\n\nDocument text:\n{text}"

        raw = self.llm_client.ask_json(
            system_prompt=self.DISCOUNT_SYSTEM_PROMPT,
            user_content=user_content,
            temperature=0.0,
            max_tokens=12000,
        )
        if not isinstance(raw, dict):
            raise RuntimeError(f"LLM returned non-JSON response: {type(raw)}")

        families = raw.get("families")
        if not isinstance(families, list):
            raise RuntimeError("LLM response missing 'families' list")
        return self._normalize_discount_rows(families)

    def parseDiscountsUsingVision(self, pdf_path: str | Path | None = None) -> list[dict[str, Any]]:
        """Extract family discount rows directly from PDF pages using a vision-capable LLM."""
        path = Path(pdf_path if pdf_path is not None else self.pdf_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if not hasattr(self.llm_client, "client") or not hasattr(self.llm_client, "model"):
            raise RuntimeError("LLM client does not support vision calls")

        try:
            import pypdfium2 as pdfium
        except Exception as exc:
            raise RuntimeError(f"Failed to import pypdfium2 for vision parsing: {exc}")

        pdf_doc = pdfium.PdfDocument(str(path))
        if len(pdf_doc) == 0:
            raise ValueError(f"Empty PDF document: {path}")

        user_blocks: list[dict[str, Any]] = [{"type": "text", "text": self.DISCOUNT_EXTRACTION_RULES}]
        for page_index in range(len(pdf_doc)):
            page = pdf_doc[page_index]
            image = page.render(scale=2.0).to_pil()
            buf = BytesIO()
            image.save(buf, format="JPEG", quality=90)
            encoded = base64.b64encode(buf.getvalue()).decode("ascii")
            user_blocks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                }
            )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.DISCOUNT_SYSTEM_PROMPT},
            {"role": "user", "content": user_blocks},
        ]
        params: dict[str, Any] = {
            "model": self.llm_client.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 12000,
            "response_format": {"type": "json_object"},
        }

        try:
            resp = self.llm_client.client.chat.completions.create(**params)
        except Exception:
            params.pop("response_format", None)
            resp = self.llm_client.client.chat.completions.create(**params)

        data = resp.model_dump() if hasattr(resp, "model_dump") else resp

        content = None
        if hasattr(self.llm_client, "get_content_text"):
            content = self.llm_client.get_content_text(data)
        if not isinstance(content, str):
            choices = data.get("choices") if isinstance(data, dict) else None
            if isinstance(choices, list) and choices:
                msg = choices[0].get("message") if isinstance(choices[0], dict) else None
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    content = msg.get("content")

        if not isinstance(content, str):
            raise RuntimeError("Vision model response has no text content")

        parsed = extract_json_from_text(content)
        if not isinstance(parsed, dict):
            try:
                parsed = json.loads(content)
            except Exception as exc:
                raise RuntimeError(f"Vision model did not return valid JSON: {exc}")

        families = parsed.get("families")
        if not isinstance(families, list):
            raise RuntimeError("Vision model response missing 'families' list")
        normalized_rows = self._normalize_discount_rows(families)

        self.pdf_path = path
        return normalized_rows

    def _normalize_discount_rows(self, families: list[Any]) -> list[dict[str, Any]]:
        normalized_rows: list[dict[str, Any]] = []
        for row in families:
            if not isinstance(row, dict):
                continue
            normalized_rows.append(self._normalize_discount_row(row))
        return normalized_rows

    def _normalize_discount_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "family_code": self._to_text(
                row.get("family_code") or row.get("familyCode") or row.get("code")
            ),
            "description": self._to_text(row.get("description") or row.get("label")),
            "quantity": self._to_number(row.get("quantity")),
            "discount": self._to_number(
                row.get("discount") or row.get("discount_rate") or row.get("discountRate")
            ),
        }

    def _to_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_number(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().replace("%", "").replace(" ", "").replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _normalize_lookup_key(self, value: Any) -> str | None:
        text = self._to_text(value)
        if not text:
            return None
        return " ".join(text.split()).casefold()

    def upsertDiscount(
        self,
        rows: list[dict[str, Any]] | None = None,
        skip_missing: bool = False,
    ) -> dict[str, Any]:
        """Update existing family rows with discount and quantity values."""
        if self.brand is None:
            raise RuntimeError("Brand context is not set. Call setBrand() first.")

        brand_id = self.brand.get("id")
        if not brand_id:
            raise RuntimeError("Current brand has no id")

        source_rows = rows if rows is not None else self.parseDiscounts()

        family_response = (
            self.supabase_client.table("family")
            .select("id,code,name")
            .eq("brand_id", brand_id)
            .execute()
        )
        if getattr(family_response, "error", None):
            raise RuntimeError(
                f"Failed to list families for brand '{brand_id}': {family_response.error}"
            )

        families = family_response.data or []
        families_by_code = {
            self._normalize_lookup_key(row.get("code")): row
            for row in families
            if self._normalize_lookup_key(row.get("code"))
        }
        families_by_name = {
            self._normalize_lookup_key(row.get("name")): row
            for row in families
            if self._normalize_lookup_key(row.get("name"))
        }

        updated = 0
        skipped = 0
        skipped_rows: list[dict[str, Any]] = []

        for index, row in enumerate(source_rows, start=1):
            family_code = self._to_text(row.get("family_code"))
            description = self._to_text(row.get("description"))
            quantity = self._to_number(row.get("quantity"))
            discount = self._to_number(row.get("discount"))

            if quantity is None or discount is None:
                missing = "quantity" if quantity is None else "discount"
                if skip_missing:
                    skipped += 1
                    skipped_rows.append(
                        {
                            "row": index,
                            "family_code": family_code,
                            "description": description,
                            "reason": f"missing {missing}",
                        }
                    )
                    continue
                raise ValueError(f"Missing {missing} for family row #{index}")

            match = None
            code_key = self._normalize_lookup_key(family_code)
            if code_key:
                match = families_by_code.get(code_key)

            if match is None:
                name_key = self._normalize_lookup_key(description)
                if name_key:
                    match = families_by_name.get(name_key)

            if match is None:
                if skip_missing:
                    skipped += 1
                    skipped_rows.append(
                        {
                            "row": index,
                            "family_code": family_code,
                            "description": description,
                            "reason": "no matching family by code or description",
                        }
                    )
                    continue
                raise ValueError(
                    f"No matching family found for row #{index} (code='{family_code}', description='{description}')"
                )

            update_result = (
                self.supabase_client.table("family")
                .update({"quantity": quantity, "discount": discount, "type": "discount"})
                .eq("id", match.get("id"))
                .execute()
            )
            if getattr(update_result, "error", None):
                raise RuntimeError(
                    f"Failed to update family '{match.get('id')}': {update_result.error}"
                )
            updated += 1

        return {
            "rows": len(source_rows),
            "deleted": 0,
            "created": 0,
            "updated": updated,
            "skipped": skipped,
            "skipped_rows": skipped_rows,
        }

    def upsetDiscount(
        self,
        rows: list[dict[str, Any]] | None = None,
        skip_missing: bool = False,
    ) -> dict[str, Any]:
        """Backward-compatible alias for upsertDiscount."""
        return self.upsertDiscount(rows=rows, skip_missing=skip_missing)

    def run(self, skip_missing: bool = False) -> dict[str, Any]:
        """Run discount import workflow: parse rows then update matching families."""
        if self.brand is None:
            raise RuntimeError("Brand context is not set. Call setBrand() first.")
        if self.pdf_path is None or self.pdf_text is None:
            raise RuntimeError("PDF is not loaded. Call load_pdf() first.")

        parsed_rows = self.parseDiscountsUsingVision()
        upsert_summary = self.upsertDiscount(parsed_rows, skip_missing=skip_missing)

        return {
            "brand_id": self.brand.get("id"),
            "brand_name": self.brand.get("name"),
            "pdf_path": str(self.pdf_path),
            "pdf_text_length": len(self.pdf_text),
            "parsed_rows": len(parsed_rows),
            **upsert_summary,
        }
