"""Compatibility wrapper for the canonical migration runner.

Historically this command accepted an optional migration file argument.
The canonical runner applies pending migrations in order and is now the
single entrypoint for migration execution.
"""

from __future__ import annotations

from script.run_migrations import run_migrations


def run_migration(migration_file=None):
    del migration_file
    run_migrations(reset=False)


if __name__ == "__main__":
    run_migration()
