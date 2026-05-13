"""Utilities for selecting the best RFP source between text and PDF attachments."""

import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.text.reader import extract_rfp_from_text
from src.pdf.extract_text import extract_text


def _normalize_rfp_data(rfp_data) -> Dict:
    if isinstance(rfp_data, list):
        return {"products": rfp_data, "contact": {}}
    if isinstance(rfp_data, str):
        try:
            import json

            parsed = json.loads(rfp_data)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"products": parsed, "contact": {}}
        except Exception:
            return {"products": [], "contact": {}}
    if isinstance(rfp_data, dict):
        # Accept canonical shape directly.
        if isinstance(rfp_data.get("products"), list):
            return rfp_data

        # Normalize nested shapes like {"ABB": {"073984": {...}}} into products[].
        products = []
        for outer_key, maybe_map in rfp_data.items():
            if not isinstance(maybe_map, dict):
                continue
            for inner_key, maybe_product in maybe_map.items():
                if not isinstance(maybe_product, dict):
                    continue
                normalized = dict(maybe_product)
                if not normalized.get("manufacturer"):
                    normalized["manufacturer"] = str(outer_key)
                if not normalized.get("part_number"):
                    normalized["part_number"] = str(inner_key)
                products.append(normalized)

        if products:
            return {"products": products, "contact": {}}
        return {"products": [], "contact": {}}
    return {"products": [], "contact": {}}


def _extract_with_cache(text: str) -> Tuple[int, Optional[Dict]]:
    """Extract RFP data using LLM and count products.
    
    Returns the real extracted count and normalized data.
    
    Parameters
    ----------
    text : str
        Text to extract from
        
    Returns
    -------
    Tuple[int, Dict | None]
        (product_count, normalized_rfp_data)
        Returns (0, None) if extraction fails or empty
    """
    if not text or not text.strip():
        return 0, None
    
    try:
        timeout_seconds = int(os.getenv("QUOTE_LLM_TIMEOUT", os.getenv("RFQ_LLM_TIMEOUT", "600")))
        rfp_data = extract_rfp_from_text(text, timeout_seconds=timeout_seconds)
        normalized = _normalize_rfp_data(rfp_data)
        product_count = len(normalized.get("products", []) or [])
        
        if product_count > 0:
            return product_count, normalized
        else:
            return 0, normalized  # Return empty but normalized structure
    except Exception as e:
        print(f"[RFPSourcePicker] Warning: LLM extraction failed: {e}")
        return 0, None


def pick_best_rfp_source(body_text: str, pdf_candidates: List[Dict]) -> Dict:
    """Pick the best RFP source between body text and PDF attachments.
    
    Extracts RFP data from each source using LLM, counts real products,
    and selects the source with most products. Caches extraction result
    to avoid re-extraction later.

    Parameters
    ----------
    body_text : str
        The email or message body text.
    pdf_candidates : List[Dict]
        List of dicts with keys: id (optional), path (Path), filename (optional).

    Returns
    -------
    Dict
        {
            "source": "text" | "pdf",
            "content": str,
            "product_count": int,
            "pdf_attachment_id": Optional[str],
            "extracted_data": Dict | None,  # Cached extraction to avoid re-extraction
        }
    """
    best_source = "text"
    best_content = body_text or ""
    best_count, best_extracted_data = _extract_with_cache(best_content)
    best_pdf_id: Optional[str] = None

    for candidate in pdf_candidates or []:
        path = candidate.get("path")
        if not path or not isinstance(path, Path) or not path.exists():
            continue

        try:
            pdf_text = extract_text(path)
            pdf_count, pdf_extracted_data = _extract_with_cache(pdf_text)
            
            if pdf_count > best_count:
                best_source = "pdf"
                best_content = pdf_text
                best_count = pdf_count
                best_extracted_data = pdf_extracted_data
                best_pdf_id = candidate.get("id")
                print(f"[RFPSourcePicker] Selected PDF (products: {pdf_count} > {best_count-pdf_count})")
        except Exception as e:
            print(f"[RFPSourcePicker] Warning: could not extract PDF: {e}")
            continue
    
    return {
        "source": best_source,
        "content": best_content,
        "product_count": best_count,
        "pdf_attachment_id": best_pdf_id,
        "extracted_data": best_extracted_data,  # Cache extraction result
    }
