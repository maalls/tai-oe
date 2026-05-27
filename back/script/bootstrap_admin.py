#!/usr/bin/env python3
"""Bootstrap first admin user safely from an existing profile."""

from __future__ import annotations

import argparse
from typing import Callable

from src.infrastructure.config.bootstrap import create_database_handler
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.repository.repository import DatabaseRepository


def _resolve_repository() -> DatabaseRepository:
    load_runtime_env(current_file=__file__)
    db_handler = create_database_handler(
        current_file=__file__,
        require_postgres_password=True,
    )
    return DatabaseRepository(db_handler)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _find_user_by_email(db: DatabaseRepository, email: str) -> dict | None:
    query = (
        "SELECT id, email, full_name, role, created_at "
        "FROM profile "
        "WHERE lower(email) = %s "
        "LIMIT 1"
    )
    rows = db.execute_dict_query(query, (_normalize_email(email),))
    return rows[0] if rows else None


def _count_admin_users(db: DatabaseRepository) -> int:
    query = "SELECT COUNT(*) AS admin_count FROM profile WHERE role = 'admin'"
    rows = db.execute_dict_query(query)
    if not rows:
        return 0
    raw_count = rows[0].get("admin_count", 0)
    try:
        return int(raw_count)
    except (TypeError, ValueError):
        return 0


def bootstrap_admin(
    *,
    email: str,
    force: bool = False,
    db: DatabaseRepository | None = None,
    out: Callable[[str], None] = print,
) -> int:
    repository = db or _resolve_repository()
    normalized_email = _normalize_email(email)

    user = _find_user_by_email(repository, normalized_email)
    if not user:
        out(f"User not found for email: {normalized_email}")
        out("No changes applied.")
        return 1

    user_id = str(user.get("id"))
    current_role = user.get("role")

    if current_role == "admin":
        out(f"User is already admin: {normalized_email} ({user_id})")
        out("No changes applied.")
        return 0

    admin_count = _count_admin_users(repository)
    if admin_count > 0 and not force:
        out("At least one admin already exists.")
        out("Refusing role overwrite without --force.")
        out(f"Target user remains role={current_role!r}: {normalized_email} ({user_id})")
        return 1

    updated = repository.set_user_role(user_id, "admin")
    if not updated:
        out(f"Failed to promote user to admin: {normalized_email} ({user_id})")
        return 1

    out(
        "Promoted user to admin: "
        f"{updated.get('email', normalized_email)} "
        f"({updated.get('id', user_id)})"
    )
    if admin_count == 0:
        out("Bootstrap completed: first admin user is now configured.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote an existing profile to admin with safety guardrails.",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email of the existing profile to promote",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwrite when admins already exist",
    )
    args = parser.parse_args()

    return bootstrap_admin(email=args.email, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
