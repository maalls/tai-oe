
import chardet
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

class CSVReader:
    """Reads CSV files with automatic encoding and delimiter detection"""

    def read(self, file: Path, offset: int = 0, limit: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Read CSV file with auto-detection of encoding and delimiter.
        
        Args:
            file: Path object to CSV file
            offset: Number of data rows to skip before collecting results
            limit: Maximum number of data rows to return (None for all)
            filters: Optional dict of {column_name: value} to include only matching rows (exact match)
            
        Returns:
            dict: Dictionary with 'headers', 'rows', 'column_metadata', and 'total' row count
        """

        # Detect encoding using a small sample to avoid scanning entire file
        with file.open('rb') as f:
            sample_bytes = f.read(32 * 1024)  # 32 KB sample is usually enough
            result = chardet.detect(sample_bytes)
            encoding = result['encoding'] or 'utf-8'
        
        # Detect delimiter
        with file.open('r', encoding=encoding, errors='replace') as f:
            sample = f.read(8192)
            try:
                sniffer = csv.Sniffer()
                # Prefer common delimiters over space
                delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
            except Exception:
                delimiter = ','
        
        # Fast count of total data rows: number of lines minus header
        total_rows = self._count_data_rows(file)

        # Read CSV with headers (apply offset/limit while streaming; optional filters)
        with file.open('r', encoding=encoding, errors='replace', newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader, [])
            rows: List[List[str]] = []
            start = max(0, offset)
            limit_val = None if limit is None else max(0, limit)

            filter_map = filters or {}
            idx_map = {col: headers.index(col) for col in filter_map.keys() if col in headers}

            filtered_total = 0

            for idx, row in enumerate(reader):
                # Apply filters first
                if idx_map:
                    match = True
                    for col, val in filter_map.items():
                        pos = idx_map.get(col)
                        if pos is None:
                            match = False
                            break
                        if pos >= len(row) or row[pos] != str(val):
                            match = False
                            break
                    if not match:
                        continue
                    filtered_total += 1
                else:
                    filtered_total += 1

                # Apply pagination after filtering
                if filtered_total <= start:
                    continue
                if limit_val is not None and len(rows) >= limit_val:
                    continue
                rows.append(row)

        
        # look for a relationship file in the same directory as the CSV file
        relation_file = file.parent / 'relations.json'
        relations = None
        reversed_relations = None
        if relation_file.exists():
            
            with relation_file.open('r', encoding='utf-8') as rf:
                
                relations = json.load(rf)
                
            # Build reversed relations: for each target sheet, list inbound relations
            
            reversed_relations = self.get_reversed_relations(relations)





        # look for the file with a .meta.json appended to the name
        meta_file = file.with_suffix(file.suffix + '.meta.json')
        metadata = None
        
        if meta_file.exists():
            
            with meta_file.open('r', encoding='utf-8') as mf:
                
                metadata = json.load(mf)
                # if hidden_columns in metadata, remove those columns from headers and rows
                hidden_columns = metadata.get('hidden_columns', [])
                if hidden_columns:
                    indices_to_remove = [headers.index(col) for col in hidden_columns if col in headers]
                    headers = [h for i, h in enumerate(headers) if i not in indices_to_remove]
                    new_rows = []
                    for row in rows:
                        new_row = [v for i, v in enumerate(row) if i not in indices_to_remove]
                        new_rows.append(new_row)
                    rows = new_rows
                
            
        
        # Compute column metadata
        null_counts = {h: 0 for h in headers}
        distinct_values = {h: set() for h in headers}
        
        for row in rows:
            for j, h in enumerate(headers):
                val = row[j] if j < len(row) else ""
                if not val or val.strip() == "":
                    null_counts[h] += 1
                else:
                    distinct_values[h].add(val)
        
        col_metadata = []
        for h in headers:
            distinct = len(distinct_values.get(h, set()))
            nulls = null_counts.get(h, 0)
            non_null = len(rows) - nulls
            is_unique = distinct > 0 and distinct == non_null if non_null > 0 else None
            is_nullable = nulls > 0
            col_metadata.append({
                "name": h,
                "distinct": distinct,
                "null_count": nulls,
                "total_sampled": len(rows),
                "is_unique": is_unique,
                "is_nullable": is_nullable,
                
            })

        return {
            "headers": headers,
            "meta": metadata,
            "rows": rows,
            "relations": relations,
            "reversed_relations": reversed_relations,
            "version": "0.1",
            "column_metadata": col_metadata,
            "total": filtered_total,
        }
    
    def get_reversed_relations(self, relations: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
        """Build reversed relations mapping from given relations."""

        reversed_relations: Dict[str, List[Dict[str, str]]] = {}
        for source_file, fields in relations.items():
            for source_field, relation in fields.items():
                target_file = relation.get('file')
                target_sheet = relation.get('sheet')
                key = relation.get('key')
                if target_sheet:
                    if target_sheet not in reversed_relations:
                        reversed_relations[target_sheet] = []
                    reversed_relations[target_sheet].append({
                        "source_file": source_file,
                        "source_field": source_field,
                        "key": key
                    })
        return reversed_relations

    def _count_data_rows(self, file: Path) -> int:
        """Count data rows quickly by counting newlines, minus one header row."""
        total = 0
        with file.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                total += chunk.count(b'\n')
        return max(0, total - 1)