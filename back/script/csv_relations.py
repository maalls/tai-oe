#!/usr/bin/env python3
"""
CSV Relations Builder

Scans a directory of CSV files, reads rows (sampled), computes per-table metadata
and infers relationships between CSV entities based on shared column names and
value overlaps.

Outputs a JSON structure:
{
  "tables": [{
    "name": "B01_COMMERCE.csv",
    "path": "/abs/path/...",
    "columns": ["REFCIALE", "GTIN", ...],
    "row_sampled": 1000,
    "distinct": { "REFCIALE": 980, "GTIN": 970, ... }
  }, ...],
  "relationships": [{
    "left_table": "B01_COMMERCE.csv",
    "left_column": "REFCIALE",
    "right_table": "C01_EXTENSION.csv",
    "right_column": "REFCIALE",
    "overlap": 850,
    "left_distinct": 980,
    "right_distinct": 900,
    "jaccard": 0.62
  }, ...]
}

Usage:
  python3 script/csv_relations.py \
    --dir var/data/electric-parts-vendor \
    --limit-rows 20000 \
    --min-overlap 10 \
    --min-jaccard 0.01 \
    --out snapshots/tmp/csv_relations.json

Notes:
- Uses only Python stdlib; optimized for sampling to keep memory reasonable.
- Relationship inference keys are based on common column names; you can hint
  known key columns with --key-columns (comma-separated) to prioritize them.
"""
import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Set


def is_csv(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".csv"


class TableMeta:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.columns: List[str] = []
        self.row_sampled: int = 0
        self.distinct: Dict[str, int] = {}
        self.values: Dict[str, Set[str]] = {}

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "columns": self.columns,
            "row_sampled": self.row_sampled,
            "distinct": self.distinct,
        }


class Relationship:
    def __init__(self, left_table: str, left_col: str, right_table: str, right_col: str,
                 overlap: int, left_distinct: int, right_distinct: int, jaccard: float):
        self.left_table = left_table
        self.left_col = left_col
        self.right_table = right_table
        self.right_col = right_col
        self.overlap = overlap
        self.left_distinct = left_distinct
        self.right_distinct = right_distinct
        self.jaccard = jaccard

    def to_dict(self) -> Dict:
        return {
            "left_table": self.left_table,
            "left_column": self.left_col,
            "right_table": self.right_table,
            "right_column": self.right_col,
            "overlap": self.overlap,
            "left_distinct": self.left_distinct,
            "right_distinct": self.right_distinct,
            "jaccard": round(self.jaccard, 6),
        }


def read_table(path: Path, limit_rows: int, prefer_columns: Optional[Set[str]]) -> TableMeta:
    meta = TableMeta(name=path.name, path=path)
    with path.open('r', encoding='utf-8', errors='replace', newline='') as handle:
        reader = csv.reader(handle)
        for index, row in enumerate(reader):
            if index == 0:
                meta.columns = [column.strip() for column in row]
                for column in meta.columns:
                    meta.values[column] = set()
                continue
            if limit_rows and meta.row_sampled >= limit_rows:
                break
            for position, column in enumerate(meta.columns):
                value = row[position] if position < len(row) else ""
                value = "" if value is None else str(value).strip()
                if prefer_columns and column in prefer_columns:
                    meta.values[column].add(value)
                elif len(meta.values[column]) < 100000:
                    meta.values[column].add(value)
            meta.row_sampled += 1
    for column in meta.columns:
        meta.distinct[column] = len(meta.values.get(column, set()))
    return meta


def infer_relationships(tables: List[TableMeta], min_overlap: int, min_jaccard: float) -> List[Relationship]:
    relationships: List[Relationship] = []
    columns_to_tables: Dict[str, List[TableMeta]] = {}
    for table in tables:
        for column in table.columns:
            columns_to_tables.setdefault(column, []).append(table)

    for column, table_list in columns_to_tables.items():
        if len(table_list) < 2:
            continue
        for left_index in range(len(table_list)):
            for right_index in range(left_index + 1, len(table_list)):
                left = table_list[left_index]
                right = table_list[right_index]
                left_values = {value for value in left.values.get(column, set()) if value != ""}
                right_values = {value for value in right.values.get(column, set()) if value != ""}
                if not left_values or not right_values:
                    continue
                overlap = len(left_values.intersection(right_values))
                if overlap < min_overlap:
                    continue
                union = len(left_values) + len(right_values) - overlap
                jaccard = (overlap / union) if union > 0 else 0.0
                if jaccard < min_jaccard:
                    continue
                relationships.append(
                    Relationship(
                        left_table=left.name,
                        left_col=column,
                        right_table=right.name,
                        right_col=column,
                        overlap=overlap,
                        left_distinct=len(left_values),
                        right_distinct=len(right_values),
                        jaccard=jaccard,
                    )
                )
    relationships.sort(key=lambda relation: (relation.overlap, relation.jaccard), reverse=True)
    return relationships


def build_graph(dir_path: Path, limit_rows: int, min_overlap: int, min_jaccard: float, key_columns: Optional[List[str]]) -> Dict:
    csv_files = sorted(path for path in dir_path.iterdir() if is_csv(path))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dir_path}")
    preferred_columns = set(column.strip() for column in key_columns) if key_columns else None
    tables = [read_table(path, limit_rows=limit_rows, prefer_columns=preferred_columns) for path in csv_files]
    relationships = infer_relationships(tables, min_overlap=min_overlap, min_jaccard=min_jaccard)
    return {
        "tables": [table.to_dict() for table in tables],
        "relationships": [relation.to_dict() for relation in relationships],
        "stats": {
            "files": len(tables),
            "relationships": len(relationships),
            "limit_rows": limit_rows,
            "min_overlap": min_overlap,
            "min_jaccard": min_jaccard,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CSV relationship graph from a folder of CSV files")
    parser.add_argument('--dir', default='var/data/electric-parts-vendor', help='Directory containing CSV files')
    parser.add_argument('--limit-rows', type=int, default=20000, help='Max rows to sample per CSV (0 = all)')
    parser.add_argument('--min-overlap', type=int, default=10, help='Minimum overlapping values to consider a relationship')
    parser.add_argument('--min-jaccard', type=float, default=0.01, help='Minimum Jaccard index to keep a relationship')
    parser.add_argument('--key-columns', default='', help='Comma-separated list of preferred key columns (e.g., REFCIALE,GTIN)')
    parser.add_argument('--out', default='', help='Output JSON path (default: stdout)')
    args = parser.parse_args()

    graph = build_graph(
        Path(args.dir).resolve(),
        limit_rows=max(0, args.limit_rows),
        min_overlap=max(1, args.min_overlap),
        min_jaccard=max(0.0, args.min_jaccard),
        key_columns=[column.strip() for column in args.key_columns.split(',') if column.strip()] if args.key_columns else [],
    )
    if args.out.strip():
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Wrote {output_path}")
        return

    print(json.dumps(graph, ensure_ascii=False))


if __name__ == '__main__':
    main()
