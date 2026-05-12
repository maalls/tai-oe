#!/usr/bin/env python3
"""
Extract products from a text or PDF file and return as JSON.

Usage:
    python extract_products_from_file.py <path_to_file>

Example:
    python extract_products_from_file.py request.txt
    python extract_products_from_file.py request.pdf
"""

import json
import sys
from pathlib import Path

from src.text.reader import extract_rfp_from_text
from src.pdf.extract_text import extract_text


def extract_products_from_file(file_path: str) -> dict:
    """
    Read a text or PDF file and extract products using the LLM.
    
    Args:
        file_path: Path to the text or PDF file
        
    Returns:
        Dictionary containing extracted products and metadata
    """
    try:
        file = Path(file_path)
        
        if not file.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}",
                "file": file_path
            }
        
        # Determine file type and read accordingly
        suffix = file.suffix.lower()
        
        if suffix == ".pdf":
            print(f"[ExtractProducts] Reading PDF file: {file_path}")
            content = extract_text(file)
        else:
            print(f"[ExtractProducts] Reading text file: {file_path}")
            content = file.read_text(encoding="utf-8")
        
        if not content.strip():
            return {
                "status": "error",
                "message": "File is empty or no text could be extracted",
                "file": file_path
            }
        
        print(f"[ExtractProducts] Content length: {len(content)} characters")
        
        # Extract products using LLM
        result = extract_rfp_from_text(content)
        
        return {
            "status": "ok",
            "file": str(file_path),
            "content_length": len(content),
            "data": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "file": file_path
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_products_from_file.py <path_to_file>")
        print("\nSupported formats: .txt, .pdf")
        print("\nExamples:")
        print("  python extract_products_from_file.py request.txt")
        print("  python extract_products_from_file.py request.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Extract products
    result = extract_products_from_file(file_path)
    
    # Output as JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "ok" else 1)
