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
  python3 scripts/csv_relations.py \
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
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

def is_csv(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".csv"

class TableMeta:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.columns: List[str] = []
        self.row_sampled: int = 0
        self.distinct: Dict[str, int] = {}
        # Store sampled sets of values per column for overlap tests
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
    # Initialize per-column value sets lazily
    with path.open('r', encoding='utf-8', errors='replace', newline='') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                meta.columns = [c.strip() for c in row]
                # initialize value sets
                for col in meta.columns:
                    meta.values[col] = set()
                continue
            if limit_rows and meta.row_sampled >= limit_rows:
                break
            for idx, col in enumerate(meta.columns):
                try:
                    val = row[idx]
                except Exception:
                    val = ""
                # normalize
                if val is None:
                    val = ""
                val = str(val).strip()
                # Heuristic: only keep values for columns that might be keys
                # Prefer hinted columns; otherwise keep values for all but cap set size
                if prefer_columns and col in prefer_columns:
                    meta.values[col].add(val)
                else:
                    # avoid giant memory: cap at 100k sampled distincts
                    if len(meta.values[col]) < 100000:
                        meta.values[col].add(val)
            meta.row_sampled += 1
    # Compute distinct counts
    for col in meta.columns:
        meta.distinct[col] = len(meta.values.get(col, set()))
    return meta

def infer_relationships(tables: List[TableMeta], min_overlap: int, min_jaccard: float) -> List[Relationship]:
    rels: List[Relationship] = []
    # Build mapping of column name -> tables that have that column
    col_map: Dict[str, List[TableMeta]] = {}
    for t in tables:
        for c in t.columns:
            col_map.setdefault(c, []).append(t)
    # For each column that appears in multiple tables, compute overlaps
    for col, tlist in col_map.items():
        if len(tlist) < 2:
            continue
        # Compare all pairs
        for i in range(len(tlist)):
            for j in range(i+1, len(tlist)):
                a = tlist[i]
                b = tlist[j]
                aset = a.values.get(col, set())
                bset = b.values.get(col, set())
                if not aset or not bset:
                    continue
                # Remove empty strings (rarely useful as keys)
                aset = {x for x in aset if x != ""}
                bset = {x for x in bset if x != ""}
                if not aset or not bset:
                    continue
                inter = aset.intersection(bset)
                overlap = len(inter)
                if overlap < min_overlap:
                    continue
                union = len(aset) + len(bset) - overlap
                jaccard = (overlap / union) if union > 0 else 0.0
                if jaccard < min_jaccard:
                    continue
                rels.append(Relationship(
                    left_table=a.name,
                    left_col=col,
                    right_table=b.name,
                    right_col=col,
                    overlap=overlap,
                    left_distinct=len(aset),
                    right_distinct=len(bset),
                    jaccard=jaccard,
                ))
    # Sort relationships by overlap desc, then jaccard desc
    rels.sort(key=lambda r: (r.overlap, r.jaccard), reverse=True)
    return rels

def build_graph(dir_path: Path, limit_rows: int, min_overlap: int, min_jaccard: float, key_columns: Optional[List[str]]) -> Dict:
    csv_files = sorted([p for p in dir_path.iterdir() if is_csv(p)])
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dir_path}")
    prefer_cols: Optional[Set[str]] = set(c.strip() for c in key_columns) if key_columns else None
    tables: List[TableMeta] = []
    for p in csv_files:
        meta = read_table(p, limit_rows=limit_rows, prefer_columns=prefer_cols)
        tables.append(meta)
    rels = infer_relationships(tables, min_overlap=min_overlap, min_jaccard=min_jaccard)
    return {
        "tables": [t.to_dict() for t in tables],
        "relationships": [r.to_dict() for r in rels],
        "stats": {
            "files": len(tables),
            "relationships": len(rels),
            "limit_rows": limit_rows,
            "min_overlap": min_overlap,
            "min_jaccard": min_jaccard,
        }
    }

def main():
    ap = argparse.ArgumentParser(description="Build CSV relationship graph from a folder of CSV files")
    ap.add_argument('--dir', default='var/data/electric-parts-vendor', help='Directory containing CSV files')
    ap.add_argument('--limit-rows', type=int, default=20000, help='Max rows to sample per CSV (0 = all)')
    ap.add_argument('--min-overlap', type=int, default=10, help='Minimum overlapping values to consider a relationship')
    ap.add_argument('--min-jaccard', type=float, default=0.01, help='Minimum Jaccard index to keep a relationship')
    ap.add_argument('--key-columns', default='', help='Comma-separated list of preferred key columns (e.g., REFCIALE,GTIN)')
    ap.add_argument('--out', default='', help='Output JSON path (default: stdout)')
    args = ap.parse_args()

    dir_path = Path(args.dir).resolve()
    limit_rows = max(0, args.limit_rows)
    min_overlap = max(1, args.min_overlap)
    min_jaccard = max(0.0, args.min_jaccard)
    key_cols = [c.strip() for c in args.key_columns.split(',') if c.strip()] if args.key_columns else []

    graph = build_graph(dir_path, limit_rows=limit_rows or 0, min_overlap=min_overlap, min_jaccard=min_jaccard, key_columns=key_cols)
    out = args.out.strip()
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open('w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path}")
    else:
        print(json.dumps(graph, ensure_ascii=False))

if __name__ == '__main__':
    main()
