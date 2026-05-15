#!/usr/bin/env python3
"""Compatibility wrapper for run_migration command."""

import sys

from src.command.run_migration import run_migration


if __name__ == "__main__":
    migration_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_migration(migration_file)
