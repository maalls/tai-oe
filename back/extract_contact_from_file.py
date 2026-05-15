#!/usr/bin/env python3
"""Compatibility wrapper for back/script/extract_contact_from_file.py."""

import json
import sys

from script.extract_contact_from_file import extract_contact_from_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_contact_from_file.py <path_to_text_file>")
        sys.exit(1)

    result = extract_contact_from_file(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "ok" else 1)
