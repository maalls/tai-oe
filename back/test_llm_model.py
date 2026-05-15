#!/usr/bin/env python3
"""Compatibility wrapper for tests/integration/llm/test_llm_model.py."""

import sys

from tests.integration.llm.test_llm_model import test_llm_model


if __name__ == "__main__":
    success = test_llm_model()
    sys.exit(0 if success else 1)
