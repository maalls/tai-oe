#!/usr/bin/env python3
"""Compatibility wrapper for tests/integration/qdrant/test_scroll_uniqueness.py."""

import runpy
from pathlib import Path


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "tests" / "integration" / "qdrant" / "test_scroll_uniqueness.py"
    runpy.run_path(str(target), run_name="__main__")
