#!/usr/bin/env python3
"""Verify that mapped CSV fields exist in the database schema."""
import argparse
from typing import Dict, Iterable, List, Tuple

from script.cli import load_config, _connect, _get_etim_mappings, _get_fabdis_mappings


def _fetch_columns(conn, table_names: Iterable[str]) -> Dict[str, set]:
    table_list = list(table_names)
    if not table_list:
        return {}
    placeholders = ",".join(["%s"] * len(table_list))
    query = (
        "SELECT table_name, column_name "
        "FROM information_schema.columns "
        f"WHERE table_schema = 'public' AND table_name IN ({placeholders})"
    )
    with conn.cursor() as cur:
        cur.execute(query, table_list)
        rows = cur.fetchall()
    columns_by_table: Dict[str, set] = {name: set() for name in table_list}
    for table_name, column_name in rows:
        columns_by_table.setdefault(table_name, set()).add(column_name)
    return columns_by_table


def _collect_mapping_columns(mappings: List[Tuple[str, str, List[Tuple[str, str]]]]):
    table_columns: Dict[str, set] = {}
    for _, table_name, columns in mappings:
        table_columns.setdefault(table_name, set()).update(db_col for _, db_col in columns)
    return table_columns


def _is_column_indexed(conn, table: str, column: str) -> bool:
    query = """
        SELECT 1
        FROM pg_index i
        JOIN pg_class t ON t.oid = i.indrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
        WHERE t.relname = %s AND a.attname = %s
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query, (table, column))
        return cur.fetchone() is not None


FABDIS_INDEX_COLUMNS: Dict[str, List[str]] = {
    "fabdis_cartouches": ["carmarque"],
    "fabdis_article": ["marque"],
    "fabdis_commerce": ["marque"],
    "fabdis_logistique": ["marque"],
    "fabdis_media": ["marque"],
    "fabdis_reglementaire": ["marque"],
    "fabdis_correspondance": ["marque"],
    "fabdis_variante": ["marque"],
    "fabdis_etim": ["marque"],
    "fabdis_extension": ["marque"],
    "fabdis_arret": ["marqueass"],
    "fabdis_substitution": ["marquesub"],
    "fabdis_pyramide": ["marquep"],
}


def verify_indexes(conn, index_columns: Dict[str, List[str]], label: str) -> int:
    missing_count = 0
    checked_count = 0
    print(f"\nVerifying {label} indexes...")
    for table_name, columns in sorted(index_columns.items()):
        for column in columns:
            checked_count += 1
            if not _is_column_indexed(conn, table_name, column):
                print(f"- {table_name}: missing index on {column}")
                missing_count += 1
            else:
                print(f"✓ {table_name}({column})")
    if missing_count == 0:
        print(f"✓ All {label} indexes exist ({checked_count} checked).")
    else:
        print(f"✗ {missing_count} missing {label} indexes ({checked_count} checked).")
    return missing_count


def verify_dataset(conn, mappings, label: str) -> int:
    table_columns = _collect_mapping_columns(mappings)
    existing = _fetch_columns(conn, table_columns.keys())
    missing_count = 0
    print(f"\nVerifying {label} mappings...")
    for table_name, expected_columns in sorted(table_columns.items()):
        actual_columns = existing.get(table_name, set())
        missing = sorted(expected_columns - actual_columns)
        if missing:
            missing_count += len(missing)
            print(f"- {table_name}: missing {', '.join(missing)}")
    if missing_count == 0:
        print(f"✓ All {label} mapped columns exist.")
    else:
        print(f"✗ {missing_count} missing columns in {label} mappings.")
    return missing_count


def main():
    parser = argparse.ArgumentParser(description="Verify mapping columns exist in database schema")
    parser.add_argument(
        "--config",
        default="/Users/malo/Documents/Projects/rkllm-server/external/rag/back/config.yml",
        help="Path to config.yml",
    )
    parser.add_argument(
        "--dataset",
        choices=["etim", "fabdis", "all"],
        default="all",
        help="Which mappings to verify",
    )
    parser.add_argument(
        "--indexes",
        action="store_true",
        help="Also verify expected FAB-DIS indexes",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    supa = cfg.get("supabase", {})
    db = supa.get("db", {})

    conn = _connect(db)
    try:
        missing = 0
        if args.dataset in ("etim", "all"):
            missing += verify_dataset(conn, _get_etim_mappings(), "ETIM")
        if args.dataset in ("fabdis", "all"):
            missing += verify_dataset(conn, _get_fabdis_mappings(), "FAB-DIS")
            if args.indexes:
                missing += verify_indexes(conn, FABDIS_INDEX_COLUMNS, "FAB-DIS")
        if missing:
            raise SystemExit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
