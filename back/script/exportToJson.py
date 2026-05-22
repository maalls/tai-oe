#!/usr/bin/env python3
"""
Export commerce table data to JSON file.

Usage:
    python exportToJson.py [--table TABLE] [--output FILE] [--where WHERE] [--limit LIMIT]

Examples:
    # Export all commerce data
    python exportToJson.py
    
    # Export specific table
    python exportToJson.py --table fabdis_cartouches
    
    # Export with WHERE clause
    python exportToJson.py --where "tarif > 100"
    
    # Export to specific file with limit
    python exportToJson.py --output products.json --limit 1000
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_service


def serialize_value(value):
    """Convert non-JSON-serializable values to serializable format."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif value is None:
        return None
    return value


def serialize_row(row: dict) -> dict:
    """Serialize a database row to JSON-compatible format."""
    return {key: serialize_value(val) for key, val in row.items()}


def export_table_to_json(
    table: str = 'fabdis_commerce',
    output_file: str = None,
    where_clause: str = None,
    limit: int = None,
    columns: str = '*'
):
    """Export table data to JSON file.
    
    Args:
        table: Table name to query
        output_file: Output JSON file path (default: {table}.json)
        where_clause: Optional WHERE clause conditions
        limit: Maximum number of rows to export
        columns: Columns to export (default: all)
    """
    # Initialize database handler from the unified config path
    database_service = create_database_service(
        current_file=__file__,
        require_postgres_password=True,
    )
    db = DatabaseHandler(database_service=database_service)
    
    # Build query
    query = f"SELECT {columns} FROM {table}"
    
    if where_clause:
        query += f" WHERE {where_clause}"
    
    if limit:
        query += f" LIMIT {limit}"
    
    print(f"Executing query: {query}")
    
    # Execute query
    try:
        rows = db.execute_dict_query(query)
        print(f"Retrieved {len(rows)} rows")
    except Exception as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Serialize data
    serialized_rows = [serialize_row(row) for row in rows]
    
    # Prepare output
    output = {
        'table': table,
        'count': len(serialized_rows),
        'columns': list(serialized_rows[0].keys()) if serialized_rows else [],
        'rows': serialized_rows
    }
    
    # Write to file
    if output_file is None:
        output_file = f"{table}.json"
    
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(serialized_rows)} rows to {output_path.absolute()}")
    print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")


def main():
    parser = argparse.ArgumentParser(
        description='Export database table to JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--table', '-t',
        default='fabdis_commerce',
        help='Table name to export (default: fabdis_commerce)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file path (default: {table}.json)'
    )
    
    parser.add_argument(
        '--where', '-w',
        help='WHERE clause conditions (e.g., "tarif > 100")'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Maximum number of rows to export'
    )
    
    parser.add_argument(
        '--columns', '-c',
        default='*',
        help='Columns to export, comma-separated (default: all)'
    )
    
    args = parser.parse_args()
    
    try:
        export_table_to_json(
            table=args.table,
            output_file=args.output,
            where_clause=args.where,
            limit=args.limit,
            columns=args.columns
        )
    except KeyboardInterrupt:
        print("\nExport cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
