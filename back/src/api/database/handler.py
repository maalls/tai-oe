"""Database request handlers."""

from typing import Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from src.infrastructure.clients.database import DatabaseHandler


class DatabaseHandlers:
    """Handlers for PostgreSQL database operations."""
    
    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler
    
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
        
        # Get optional parameters
        columns_raw = (qs.get('columns') or ['*'])[0]
        where_clause = (qs.get('where') or [''])[0]
        sort_by = (qs.get('sortBy') or [''])[0]
        limit = int((qs.get('limit') or ['100'])[0])
        offset = int((qs.get('offset') or ['0'])[0])
        
        # Validate and sanitize
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        
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
