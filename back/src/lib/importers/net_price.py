"""
Net Price Importer for updating family entries from PDF files using LLM extraction.
"""

from pathlib import Path
from typing import Any

from pypdf import PdfReader


class NetPriceImporter:
    """Imports and updates net price information for families from PDF files."""

    def __init__(self, supabase_client, llm_client):
        """
        Initialize the NetPriceImporter.
        
        Args:
            supabase_client: table-compatible database client for persistence operations
            llm_client: LLM client for PDF text extraction and parsing
        """
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

    def parseNetPrices(self, source_text: str | None = None) -> list[dict[str, Any]]:
        """Extract product table rows (code, local code, description, quantity, net price) from PDF text."""
        text = (source_text or self.pdf_text or "").strip()
        if not text:
            raise ValueError("No text available to parse. Call load_pdf() first or pass source_text.")

        system_prompt = (
            "You extract product rows from supplier pricing documents. "
            "Return only valid JSON and no extra text."
        )

        user_content = (
            "Extract the product table from the text below. Ignore all non-product sections.\n"
            "For each product row, return these exact fields:\n"
            "- product_code\n"
            "- description\n"
            "- quantity\n"
            "- net_price\n"
            "- total_price\n\n"
            "Rules:\n"
            "- Output strictly this JSON shape: {\"products\": [ ... ]}.\n"
            "- if for a single product, multiple codes are found, put shortest code available.\n"
            "- net price may be refered as unit price\n"
            "- total price should be quantity * net price if available in the text, otherwise null.\n"
            "- net price should be total_price / quantity if total price is available.\n"
            "- Keep product_code/description as strings.\n"
            "- quantity and net_price should be numeric using either dot or comma as decimal separator.\n"
            "- If a field is missing in a row, use null.\n"
            "- Do not invent products.\n\n"
            "Document text:\n"
            f"{text}"
        )

        raw = self.llm_client.ask_json(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.0,
            max_tokens=12000,
        )
        if not isinstance(raw, dict):
            raise RuntimeError(f"LLM returned non-JSON response: {type(raw)}")

        products = raw.get("products")
        if not isinstance(products, list):
            raise RuntimeError("LLM response missing 'products' list")

        normalized_rows = []
        for row in products:
            if not isinstance(row, dict):
                continue

            normalized_rows.append(
                {
                    "product_code": self._to_text(
                        row.get("product_code")
                        or row.get("productCode")
                        or row.get("code")
                    ),
                    "local_code": self._to_text(
                        row.get("local_code")
                        or row.get("localCode")
                        or row.get("code_local")
                    ),
                    "description": self._to_text(row.get("description") or row.get("label")),
                    "quantity": self._to_number(row.get("quantity")),
                    "net_price": self._to_number(
                        row.get("net_price") or row.get("netPrice") or row.get("price")
                    ),
                }
            )

        return normalized_rows

    def upsertNetPrices(self, rows: list[dict[str, Any]] | None = None) -> dict[str, int]:
        """Replace brand net price families using parsed product rows."""
        if self.brand is None:
            raise RuntimeError("Brand context is not set. Call setBrand() first.")

        brand_id = self.brand.get("id")
        if not brand_id:
            raise RuntimeError("Current brand has no id")

        source_rows = rows if rows is not None else self.parseNetPrices()

        existing_response = (
            self.supabase_client.table("family")
            .select("id")
            .eq("brand_id", brand_id)
            .eq("type", "net_price")
            .execute()
        )
        if getattr(existing_response, "error", None):
            raise RuntimeError(
                f"Failed to list existing net_price families for brand '{brand_id}': {existing_response.error}"
            )

        deleted = 0
        if existing_response.data:
            delete_result = (
                self.supabase_client.table("family")
                .delete()
                .eq("brand_id", brand_id)
                .eq("type", "net_price")
                .execute()
            )
            if getattr(delete_result, "error", None):
                raise RuntimeError(
                    f"Failed to delete existing net_price families for brand '{brand_id}': {delete_result.error}"
                )
            deleted = len(existing_response.data)

        created = 0

        for index, row in enumerate(source_rows, start=1):
            product_code = self._to_text(row.get("product_code"))
            if not product_code:
                raise ValueError(
                    f"Missing product_code for net price row #{index}"
                )

            quantity = self._to_number(row.get("quantity"))
            net_price = self._to_number(row.get("net_price"))
            if quantity is None:
                raise ValueError(
                    f"Missing quantity for product_code '{product_code}' (row #{index})"
                )
            if net_price is None:
                raise ValueError(
                    f"Missing net_price for product_code '{product_code}' (row #{index})"
                )

            insert_data = {
                "brand_id": brand_id,
                "type": "net_price",
                "product_code": product_code,
                "name": self._to_text(row.get("description")) or product_code,
                "quantity": quantity,
                "net_price": net_price,
            }
            result = self.supabase_client.table("family").insert(insert_data).execute()
            if getattr(result, "error", None):
                raise RuntimeError(
                    f"Failed to create net_price family '{product_code}': {result.error}"
                )
            created += 1

        return {
            "rows": len(source_rows),
            "deleted": deleted,
            "created": created,
            "updated": 0,
            "skipped": 0,
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

        text = str(value).strip().replace(" ", "").replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def run(self) -> dict:
        """Run net price import workflow: parse PDF rows and upsert net price families."""
        if self.brand is None:
            raise RuntimeError("Brand context is not set. Call setBrand() first.")
        if self.pdf_path is None or self.pdf_text is None:
            raise RuntimeError("PDF is not loaded. Call load_pdf() first.")

        parsed_rows = self.parseNetPrices()
        upsert_summary = self.upsertNetPrices(parsed_rows)

        return {
            "brand_id": self.brand.get("id"),
            "brand_name": self.brand.get("name"),
            "pdf_path": str(self.pdf_path),
            "pdf_text_length": len(self.pdf_text),
            "parsed_rows": len(parsed_rows),
            **upsert_summary,
        }
