#!/usr/bin/env python3
"""
Extract contact and company information from a text file and return as JSON.

Usage:
    python back/script/extract_contact_from_file.py <path_to_text_file>

Example:
    python back/script/extract_contact_from_file.py request.txt
"""

import json
import sys
from pathlib import Path

from src.lib.extractors.text_reader import extract_company_from_text


def extract_contact_from_file(file_path: str) -> dict:
    """
    Read a text file and extract contact/company information using the LLM.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Dictionary containing extracted contact and company information
    """
    try:
        file = Path(file_path)
        
        if not file.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}",
                "file": file_path
            }
        
        # Read the file
        content = file.read_text(encoding="utf-8")
        
        if not content.strip():
            return {
                "status": "error",
                "message": "File is empty",
                "file": file_path
            }
        
        print(f"[ExtractContact] Reading file: {file_path}")
        print(f"[ExtractContact] Content length: {len(content)} characters")
        
        # Extract contact and company info using LLM
        result = extract_company_from_text(content)
        
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
        print("Usage: python extract_contact_from_file.py <path_to_text_file>")
        print("\nExample:")
        print("  python extract_contact_from_file.py request.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Extract contact and company info
    result = extract_contact_from_file(file_path)
    
    # Output as JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "ok" else 1)
