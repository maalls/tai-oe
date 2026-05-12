#!/usr/bin/env python3
"""
CLI tool for database migrations.

Usage:
    python src/command/migrations_cli.py status
    python src/command/migrations_cli.py up
    python src/command/migrations_cli.py apply <migration_name>
    python src/command/migrations_cli.py list
"""

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import psycopg2
from dotenv import load_dotenv

load_dotenv()


class MigrationManager:
    def __init__(self):
        self.migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL must be set in environment variables")

    def connect(self):
        return psycopg2.connect(self.db_url)

    def ensure_migrations_table(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                  id SERIAL PRIMARY KEY,
                  migration_name TEXT NOT NULL UNIQUE,
                  executed_at TIMESTAMP DEFAULT NOW(),
                  checksum TEXT,
                  CONSTRAINT unique_migration_name UNIQUE(migration_name)
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_migrations_name
                ON migrations(migration_name);
                """
            )
        conn.commit()

    def list_migration_files(self) -> List[Path]:
        if not self.migrations_dir.exists():
            return []
        return sorted(self.migrations_dir.glob("*.sql"))

    def compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_applied_migrations(self, conn) -> Dict[str, Tuple[str, datetime]]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT migration_name, checksum, executed_at FROM migrations ORDER BY id ASC;"
            )
            rows = cur.fetchall()
        return {row[0]: (row[1], row[2]) for row in rows}

    def status(self):
        with self.connect() as conn:
            self.ensure_migrations_table(conn)
            applied = self.get_applied_migrations(conn)

        files = self.list_migration_files()
        if not files:
            print("No migration files found in migrations/")
            return

        print("\nMigration Status")
        print("=" * 60)
        for file_path in files:
            name = file_path.name
            if name in applied:
                checksum, executed_at = applied[name]
                print(f"✓ {name} (applied at {executed_at})")
            else:
                print(f"✗ {name} (pending)")

    def list(self):
        with self.connect() as conn:
            self.ensure_migrations_table(conn)
            applied = self.get_applied_migrations(conn)

        if not applied:
            print("No migrations applied yet.")
            return

        print("\nApplied Migrations")
        print("=" * 60)
        for name, (checksum, executed_at) in applied.items():
            checksum_display = checksum[:12] + "..." if checksum else "(none)"
            print(f"{name} | {executed_at} | {checksum_display}")

    def apply_migration(self, migration_path: Path):
        if not migration_path.exists():
            print(f"Migration file not found: {migration_path}")
            return

        sql = migration_path.read_text()
        checksum = self.compute_checksum(sql)

        with self.connect() as conn:
            self.ensure_migrations_table(conn)
            applied = self.get_applied_migrations(conn)

            if migration_path.name in applied:
                existing_checksum, executed_at = applied[migration_path.name]
                if existing_checksum and existing_checksum != checksum:
                    print(
                        f"⚠ {migration_path.name} already applied at {executed_at} "
                        "but checksum differs. Skipping."
                    )
                else:
                    print(f"✓ {migration_path.name} already applied. Skipping.")
                return

            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        """
                        INSERT INTO migrations (migration_name, executed_at, checksum)
                        VALUES (%s, %s, %s);
                        """,
                        (migration_path.name, datetime.now(timezone.utc), checksum),
                    )
                conn.commit()
                print(f"✓ Applied {migration_path.name}")
            except Exception as e:
                conn.rollback()
                print(f"✗ Failed to apply {migration_path.name}: {e}")
                raise

    def up(self):
        files = self.list_migration_files()
        if not files:
            print("No migration files found in migrations/")
            return

        with self.connect() as conn:
            self.ensure_migrations_table(conn)
            applied = self.get_applied_migrations(conn)

        pending = [f for f in files if f.name not in applied]
        if not pending:
            print("No pending migrations.")
            return

        for migration in pending:
            self.apply_migration(migration)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    manager = MigrationManager()

    if command == "status":
        manager.status()
    elif command == "list":
        manager.list()
    elif command == "up":
        manager.up()
    elif command == "apply":
        if len(sys.argv) < 3:
            print("Usage: migrations_cli.py apply <migration_name>")
            return
        migration_name = sys.argv[2].replace("migrations/", "").replace("migrations\\", "")
        manager.apply_migration(manager.migrations_dir / migration_name)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
