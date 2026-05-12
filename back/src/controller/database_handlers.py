"""Database request handlers."""

from typing import Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from src.controller.db_client import DatabaseHandler


class DatabaseHandlers:
    """Handlers for PostgreSQL database operations."""
    
    def __init__(self, db_handler: Optional[DatabaseHandler] = None, qdrant_handler=None):
        self.db_handler = db_handler
        self.qdrant_handler = qdrant_handler
    
    @staticmethod
    def serialize_value(value):
        """Convert non-JSON-serializable values to serializable format."""
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif value is None:
            return None
        return value
    
    @staticmethod
    def serialize_row(row: Dict) -> Dict:
        """Serialize a database row to JSON-compatible format."""
        return {key: DatabaseHandlers.serialize_value(val) for key, val in row.items()}
    
    def handle_query(self, qs: Dict) -> Dict:
        """Handle database query requests.
        
        Query parameters:
            table: Table name to query
            columns: Comma-separated list of columns (optional, defaults to all)
            where: WHERE clause conditions (optional)
            sortBy: ORDER BY clause (e.g., "price ASC", "name DESC") (optional)
            limit: Maximum number of rows (default 100, max 1000)
            offset: Number of rows to skip (default 0)
            
        Returns:
            Dict with 'columns' and 'rows' keys
        """
        if not self.db_handler:
            return {"error": "Database handler not configured"}
        
        if qs.get('tables') is not None:
            # return the list of tables with their columns and metadata
            query = """
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale
                FROM information_schema.tables t
                LEFT JOIN information_schema.columns c 
                    ON t.table_name = c.table_name 
                    AND t.table_schema = c.table_schema
                WHERE t.table_schema = 'public'
                ORDER BY t.table_name, c.ordinal_position;
            """
            rows = self.db_handler.execute_dict_query(query)
            
            # Group columns by table
            tables = {}
            for row in rows:
                table_name = row['table_name']
                if table_name not in tables:
                    tables[table_name] = {
                        'name': table_name,
                        'columns': []
                    }
                
                if row['column_name']:  # Only add if column exists
                    tables[table_name]['columns'].append({
                        'name': row['column_name'],
                        'type': row['data_type'],
                        'nullable': row['is_nullable'] == 'YES',
                        'default': row['column_default'],
                        'max_length': row['character_maximum_length'],
                        'precision': row['numeric_precision'],
                        'scale': row['numeric_scale']
                    })
            
            return {'tables': list(tables.values())}

        table = (qs.get('table') or [None])[0]
        if not table:
            return {"error": "Missing 'table' parameter"}
        
        # Check if this is a Qdrant collection (fallback to Qdrant if table not found in PostgreSQL)
        # Try PostgreSQL first, but if it fails with table not found, check Qdrant
        
        # Get optional parameters
        columns_raw = (qs.get('columns') or ['*'])[0]
        where_clause = (qs.get('where') or [''])[0]
        sort_by = (qs.get('sortBy') or [''])[0]
        limit = int((qs.get('limit') or ['100'])[0])
        offset = int((qs.get('offset') or ['0'])[0])
        
        # Validate and sanitize
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        
        # Try Qdrant collection first if qdrant_handler is available
        if self.qdrant_handler:
            try:
                from src.controller.qdrant_client import QdrantClient
                qdrant_client = QdrantClient()
                collections = qdrant_client.get_collections()
                collection_names = [c.name for c in collections.collections] if hasattr(collections, 'collections') else []
                
                if table in collection_names:
                    return self._query_qdrant_collection(table, columns_raw, where_clause, limit, offset)
            except Exception:
                pass  # Fallback to PostgreSQL
        
        # Build PostgreSQL query
        columns = columns_raw if columns_raw != '*' else '*'
        query = f"SELECT {columns} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if sort_by:
            query += f" ORDER BY {sort_by}"
        
        query += f" LIMIT {limit} OFFSET {offset}"
        
        try:
            results = self.db_handler.execute_dict_query(query)
            
            # Serialize results to handle date/datetime/decimal objects
            serialized_results = [self.serialize_row(row) for row in results]
            
            # Extract column names if available
            if serialized_results:
                columns_list = list(serialized_results[0].keys())
            else:
                columns_list = []
            
            return {
                "columns": columns_list,
                "rows": serialized_results,
                "count": len(serialized_results),
                "offset": offset,
                "limit": limit
            }
        except Exception as e:
            import traceback
            print(f"CSV Query Error: {e}", flush=True)
            print(f"Query: {query}", flush=True)
            traceback.print_exc()
            return {"error": str(e)}
    
    def handle_search(self, qs: Dict, embedding_generator) -> Dict:
        """Handle vector search with optional column sorting.
        
        Query parameters:
            q: Search query text (required)
            top_k: Number of results (default 5, max 100)
            sort_by: Column name to sort by (optional)
            sort_order: Sort order 'asc' or 'desc' (default 'asc')
        """
        if not self.db_handler:
            return {"error": "Database handler not configured"}
        
        query = (qs.get('q') or [None])[0]
        if not query:
            return {"error": "Missing 'q' parameter"}
        top_k = int((qs.get('top_k') or ['5'])[0])
        top_k = max(1, min(top_k, 100))
        
        sort_by = (qs.get('sort_by') or [None])[0]
        sort_order = (qs.get('sort_order') or ['asc'])[0].lower()
        
        if sort_order not in ['asc', 'desc']:
            return {"error": "sort_order must be 'asc' or 'desc'"}
        
        try:
            query_vector = embedding_generator.generate_embedding(query)
            results = self.db_handler.vector_search(query_vector, top_k=top_k)
            
            # Sort results if sort_by is specified
            if sort_by and isinstance(results, list) and len(results) > 0:
                # Check if the column exists in the first result
                if isinstance(results[0], dict) and sort_by in results[0]:
                    reverse = (sort_order == 'desc')
                    results.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
                else:
                    return {"error": f"Column '{sort_by}' not found in results"}
            
            return {"results": results}
        except Exception as e:
            return {"error": str(e)}
    
    def _query_qdrant_collection(self, collection: str, columns_raw: str, where_clause: str, limit: int, offset: int) -> Dict:
        """Query a Qdrant collection with text filtering.
        
        Args:
            collection: Collection name
            columns_raw: Comma-separated columns to return (or '*' for all)
            where_clause: WHERE clause for text filtering (e.g., "field ILIKE '%pattern%'")
            limit: Max results
            offset: Pagination offset
            
        Returns:
            Dict with 'columns' and 'rows' keys
        """
        try:
            from src.controller.qdrant_client import QdrantClient
            import re
            
            qdrant_client = QdrantClient()
            
            # Scroll through collection to get all points
            points = []
            offset_scroll = 0
            total_limit = limit + offset + 100  # Get extra to account for filtering
            
            while len(points) < total_limit:
                response = qdrant_client.scroll(collection, limit=min(100, total_limit - len(points)), offset=offset_scroll)
                if not response.points:
                    break
                points.extend(response.points)
                offset_scroll += len(response.points)
            
            # Convert points to dictionaries
            rows = []
            for point in points:
                payload = point.payload if hasattr(point, 'payload') else {}
                rows.append(payload)
            
            # Apply WHERE clause filtering if provided
            if where_clause:
                rows = self._filter_rows_by_where_clause(rows, where_clause)
            
            # Extract columns
            if rows:
                if columns_raw == '*':
                    columns_list = list(rows[0].keys())
                else:
                    columns_list = [c.strip() for c in columns_raw.split(',')]
                    # Filter rows to only include specified columns
                    rows = [{col: row.get(col) for col in columns_list if col in row} for row in rows]
            else:
                columns_list = [c.strip() for c in columns_raw.split(',')] if columns_raw != '*' else []
            
            # Apply pagination
            paginated_rows = rows[offset:offset + limit]
            
            return {
                "columns": columns_list,
                "rows": paginated_rows,
                "count": len(paginated_rows),
                "offset": offset,
                "limit": limit
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Qdrant query failed: {str(e)}"}
    
    def _filter_rows_by_where_clause(self, rows: list, where_clause: str) -> list:
        """Filter rows using a WHERE clause pattern.
        
        Supports simple patterns like:
            - field ILIKE '%pattern%'
            - field = 'value'
            - field LIKE '%pattern'
        """
        if not where_clause:
            return rows
        
        filtered = []
        for row in rows:
            if self._matches_where_clause(row, where_clause):
                filtered.append(row)
        
        return filtered
    
    def _matches_where_clause(self, row: dict, where_clause: str) -> bool:
        """Check if a row matches the WHERE clause."""
        # Parse simple ILIKE patterns: "field ILIKE '%pattern%'"
        import re
        
        # Match ILIKE pattern: field ILIKE '%...%'
        ilike_match = re.match(r"(\w+)\s+ILIKE\s+'([^']+)'", where_clause, re.IGNORECASE)
        if ilike_match:
            field = ilike_match.group(1)
            pattern = ilike_match.group(2).replace('%', '')  # Remove % wildcards
            value = str(row.get(field, '')).lower()
            pattern_lower = pattern.lower()
            return pattern_lower in value
        
        # Match exact equality: field = 'value'
        eq_match = re.match(r"(\w+)\s*=\s*'([^']+)'", where_clause)
        if eq_match:
            field = eq_match.group(1)
            pattern = eq_match.group(2)
            return str(row.get(field, '')) == pattern
        
        # Match LIKE pattern: field LIKE '%...%'
        like_match = re.match(r"(\w+)\s+LIKE\s+'([^']+)'", where_clause, re.IGNORECASE)
        if like_match:
            field = like_match.group(1)
            pattern = like_match.group(2).replace('%', '')
            value = str(row.get(field, ''))
            return pattern in value
        
        return True  # If no pattern matches, include the row
