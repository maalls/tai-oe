#!/usr/bin/env python3
"""Compatibility wrapper for the canonical migration runner.

This command now delegates to script.run_migrations so there is a single
migration entrypoint and a single DB configuration path.
"""

from __future__ import annotations

import sys

from script.run_migrations import run_migrations


def main() -> int:
    args = set(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print("Usage: python -m src.command.migrations_cli [--reset]")
        return 0

    if any(arg in args for arg in ("status", "up", "list", "apply")):
        print(
            "This command is now unified with script.run_migrations. "
            "Use '--reset' when you want to re-run recorded migrations."
        )

    reset = "--reset" in args
    run_migrations(reset=reset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
