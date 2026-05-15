#!/usr/bin/env python3
"""Backward-compatible wrapper around src.api.server.

Kept to avoid breaking existing launch commands using ``python -m src.controller.rag``.
"""

from src.api.server import (
    ReusableThreadingHTTPServer,
    config,
    create_rag_handler,
    main,
    make_handler,
    test_llm_connection,
)

__all__ = [
    "ReusableThreadingHTTPServer",
    "config",
    "create_rag_handler",
    "main",
    "make_handler",
    "test_llm_connection",
]

if __name__ == '__main__':
    main()
