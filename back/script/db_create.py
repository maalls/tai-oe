import argparse
import os
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.infrastructure.config.bootstrap import create_database_service
from src.infrastructure.runtime.env_loader import load_runtime_env

from script.cli import _connect


CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\w+\.)?\"?([a-zA-Z_][\w$]*)\"?",
    re.IGNORECASE,
)
REFERENCES_RE = re.compile(
    r"REFERENCES\s+(?:\w+\.)?\"?([a-zA-Z_][\w$]*)\"?",
    re.IGNORECASE,
)
ALTER_TABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:\w+\.)?\"?([a-zA-Z_][\w$]*)\"?",
    re.IGNORECASE,
)


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return sql


def _load_schema_files(schema_dir: Path, include_fabdis: bool = False) -> list[Path]:
    files = sorted([p for p in schema_dir.rglob("*.sql") if p.is_file()])
    skipped = []
    filtered = []

    for file_path in files:
        rel_path = file_path.relative_to(schema_dir)
        rel = rel_path.as_posix()

        # Legacy monolithic schema conflicts with split files; keep split files as source of truth.
        if rel_path.name == "documents.sql":
            skipped.append(rel)
            continue

        # FAB-DIS schema is optional and excluded by default.
        if not include_fabdis and rel.startswith("tables/fabdis/"):
            skipped.append(rel)
            continue
        filtered.append(file_path)

    if skipped:
        print("Skipping legacy schema files:")
        for rel in skipped:
            print(f"  - {rel}")

    def sort_key(file_path: Path):
        rel = file_path.relative_to(schema_dir).as_posix()
        if rel.startswith("types/"):
            priority = 0
        elif rel.startswith("tables/"):
            priority = 1
        else:
            priority = 2
        return (priority, rel)

    files = sorted(filtered, key=sort_key)
    if not files:
        print(f"No SQL files found in: {schema_dir}")
        sys.exit(1)
    return files


def _file_metadata(sql_file: Path, schema_dir: Path) -> dict:
    content = sql_file.read_text(encoding="utf-8")
    normalized = _strip_sql_comments(content)
    creates = {m.group(1).lower() for m in CREATE_TABLE_RE.finditer(normalized)}
    refs = {m.group(1).lower() for m in REFERENCES_RE.finditer(normalized)}
    alters = {m.group(1).lower() for m in ALTER_TABLE_RE.finditer(normalized)}

    needs = (refs | alters) - creates
    file_id = sql_file.relative_to(schema_dir).as_posix()
    return {
        "id": file_id,
        "path": sql_file,
        "content": content,
        "creates": creates,
        "needs": needs,
    }


def _toposort_files(metadata: list[dict]) -> tuple[list[dict], list[str]]:
    by_id = {item["id"]: item for item in metadata}

    table_to_files = defaultdict(set)
    for item in metadata:
        for table in item["creates"]:
            table_to_files[table].add(item["id"])

    dependencies = {item["id"]: set() for item in metadata}
    warnings: list[str] = []

    for item in metadata:
        file_id = item["id"]
        for needed_table in item["needs"]:
            creators = table_to_files.get(needed_table, set())
            if not creators:
                continue
            if len(creators) > 1:
                warnings.append(
                    f"Ambiguous creators for table '{needed_table}' used by '{file_id}': "
                    f"{', '.join(sorted(creators))}"
                )
                continue
            creator = next(iter(creators))
            if creator != file_id:
                dependencies[file_id].add(creator)

    indegree = {name: len(dependencies[name]) for name in dependencies}
    reverse_graph = defaultdict(set)
    for name, deps in dependencies.items():
        for dep in deps:
            reverse_graph[dep].add(name)

    queue = deque(sorted([name for name, deg in indegree.items() if deg == 0]))
    ordered_names: list[str] = []

    while queue:
        current = queue.popleft()
        ordered_names.append(current)
        for dependent in sorted(reverse_graph[current]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(ordered_names) != len(metadata):
        remaining = sorted(set(by_id.keys()) - set(ordered_names))
        warnings.append(
            "Could not fully resolve dependency graph. Appending unresolved files in alphabetical order: "
            + ", ".join(remaining)
        )
        ordered_names.extend(remaining)

    return [by_id[name] for name in ordered_names], warnings


def _order_by_dependencies(schema_files: list[Path], schema_dir: Path) -> tuple[list[dict], list[str]]:
    metadata = [_file_metadata(f, schema_dir) for f in schema_files]
    types_meta = [item for item in metadata if item["id"].startswith("types/")]
    non_types_meta = [item for item in metadata if not item["id"].startswith("types/")]

    ordered_types, type_warnings = _toposort_files(types_meta)
    ordered_non_types, non_type_warnings = _toposort_files(non_types_meta)
    return ordered_types + ordered_non_types, type_warnings + non_type_warnings


def _drop_all_public_tables(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        table_names = [row[0] for row in cur.fetchall()]

        if not table_names:
            print("No existing public tables to drop.")
            return

        print(f"Dropping {len(table_names)} existing public table(s)...")
        for table_name in table_names:
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        conn.commit()
        print("Existing public tables dropped.")


def _ensure_required_extensions(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    conn.commit()
    print("Required extensions ensured (pgcrypto).")


def _execute_sql_files(conn, ordered_files: list[dict]) -> list[str]:
    failed_files: list[str] = []
    with conn.cursor() as cur:
        for item in ordered_files:
            file_name = item["id"]
            print(f"Applying {file_name}...")
            try:
                cur.execute(item["content"])
                conn.commit()
                print(f"  OK: {file_name}")
            except Exception as exc:
                conn.rollback()
                print(f"  ERROR in {file_name}: {exc}")
                failed_files.append(file_name)
    return failed_files


def _confirm_destructive_action(force: bool = False) -> None:
    print("\nWARNING: This operation will DROP ALL existing tables in schema 'public'.")
    print("WARNING: Data in dropped tables will be permanently deleted.")
    print("WARNING: Then all SQL files in back/schema will be executed.\n")

    if force:
        print("Force mode enabled: skipping interactive confirmation.")
        return

    answer = input("Type 'DELETE' to continue: ").strip()
    if answer != "DELETE":
        print("Aborted. No changes were applied.")
        sys.exit(1)


def _db_from_url(database_url: str) -> dict:
    try:
        parsed = urlparse(database_url)
        if parsed.scheme not in ("postgres", "postgresql"):
            print("Invalid DATABASE_URL scheme. Use postgres:// or postgresql://")
            sys.exit(1)

        db = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": (parsed.path or "").lstrip("/") or None,
            "user": parsed.username,
            "password": unquote(parsed.password) if parsed.password else None,
            "sslmode": "prefer",
        }

        required = ["host", "user", "password", "database"]
        missing = [k for k in required if not db.get(k)]
        if missing:
            print("DATABASE_URL is missing required parts:")
            print(f"  - {', '.join(missing)}")
            print("Expected format: postgresql://user:password@host:port/database")
            sys.exit(1)

        return db
    except Exception:
        print("Invalid DATABASE_URL value.")
        print("Expected format: postgresql://user:password@host:port/database")
        sys.exit(1)


def _resolve_db_config() -> dict:
    load_runtime_env(current_file=__file__)
    try:
        database_service = create_database_service(
            current_file=__file__,
            require_postgres_password=True,
        )
        source, database_url = database_service.resolve_migration_db_url()
    except Exception as exc:
        print("Failed to resolve migration DB profile from SUPABASE_ENV_FILE.")
        print(f"Error: {exc}")
        sys.exit(1)

    print(f"Using database settings from migration profile source: {source}")
    return _db_from_url(database_url)


def create_tables_from_schema(
    schema_dir: str | None = None,
    force: bool = False,
    include_fabdis: bool = False,
) -> None:
    db = _resolve_db_config()

    base_dir = Path(__file__).resolve().parent.parent
    schema_path = Path(schema_dir) if schema_dir else base_dir / "schema"
    if not schema_path.is_absolute():
        schema_path = base_dir / schema_path
    schema_path = schema_path.resolve()

    if not schema_path.exists() or not schema_path.is_dir():
        print(f"Schema directory not found: {schema_path}")
        sys.exit(1)

    sql_files = _load_schema_files(schema_path, include_fabdis=include_fabdis)
    ordered_files, warnings = _order_by_dependencies(sql_files, schema_path)

    if warnings:
        print("Dependency warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"Found {len(sql_files)} SQL file(s) in {schema_path}")
    print("Execution order:")
    for item in ordered_files:
        print(f"  - {item['id']}")

    _confirm_destructive_action(force=force)

    try:
        conn = _connect(db)
    except Exception as exc:
        print("Failed to connect to PostgreSQL.")
        print(f"Connection details: host={db.get('host')} port={db.get('port')} database={db.get('database')} user={db.get('user')}")
        print(f"Error: {exc}")
        sys.exit(1)

    try:
        _drop_all_public_tables(conn)
        _ensure_required_extensions(conn)

        failed = _execute_sql_files(conn, ordered_files)
        if failed:
            print("\nRetrying failed files once after initial pass...")
            retry_items = [i for i in ordered_files if i["id"] in failed]
            still_failed = _execute_sql_files(conn, retry_items)
            if still_failed:
                print("\nSchema apply completed with errors in:")
                for file_name in still_failed:
                    print(f"  - {file_name}")
                sys.exit(1)

        print("\nAll schema SQL files applied successfully.")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="db_create",
        description="Drop all public tables, then recreate schema from back/schema SQL files.",
    )
    parser.add_argument(
        "--schema-dir",
        dest="schema_dir",
        default=None,
        help="Path to schema directory (default: back/schema)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip interactive confirmation before dropping all public tables.",
    )
    parser.add_argument(
        "--include-fabdis",
        action="store_true",
        help="Include FAB-DIS schema files from tables/fabdis (excluded by default).",
    )

    args = parser.parse_args()
    create_tables_from_schema(
        schema_dir=args.schema_dir,
        force=args.force,
        include_fabdis=args.include_fabdis,
    )


if __name__ == "__main__":
    main()
