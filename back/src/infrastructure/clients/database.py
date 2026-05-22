"""Database connection handler for PostgreSQL/Supabase."""

import os
from pathlib import Path
import yaml
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import find_dotenv
from src.infrastructure.config.models import ResolvedRuntimeConfig
from src.infrastructure.config.provider import ConfigProvider
from src.infrastructure.config.service import DatabaseService


def load_config_yaml(filename="config.yml"):
    # Try to find config.yml in common locations
    search_paths = [
        Path(__file__).parent / filename,  # same dir as this file
        Path(__file__).parent.parent / filename,  # one level up
        Path.cwd() / filename,  # current working dir
        Path.cwd() / "back" / filename,  # ./back/config.yml
    ]
    for path in search_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(f"config.yml not found in: {[str(p) for p in search_paths]}")

# Usage:
# config = load_config_yaml()

# Try to import psycopg2, fallback to pg8000
_pg_driver = None
try:
    import psycopg2
    import psycopg2.extras
    _pg_driver = "psycopg2"
except ImportError:
    try:
        import pg8000
        _pg_driver = "pg8000"
    except ImportError:
        raise ImportError("Missing DB driver. Install one of: psycopg2-binary or pg8000")


class DatabaseHandler:
    """Handles PostgreSQL/Supabase database connections and queries."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        database_service: Optional[DatabaseService] = None,
    ):
        """Initialize database handler with configuration.
        
        Args:
            config_path: Path to YAML config file. If None, uses default 'config.yml'
        """
        if database_service is None:
            raise ValueError("DatabaseHandler requires an injected database_service")

        if config is not None:
            self.config = config
            self.db_config = self._get_db_config()
        else:
            self.config_path = config_path or self._find_config()
            self.config = self._load_config()
            self.db_config = self._get_db_config()
        self._database_service = database_service
        self._connection = None
        print(f"DatabaseHandler initialized with config: {self.db_config}")
        #print("connecting using the following config:", self.db_config, self.config_path, self.config)
    
    def _find_config(self) -> str:
        """Find config.yml in standard locations."""
        # Try relative to current file
        current_dir = Path(__file__).parent.parent.parent
        config_candidates = [
            current_dir / 'config.yml',
            Path.cwd() / 'config.yml',
            Path.cwd() / 'back' / 'config.yml',
        ]
        
        for candidate in config_candidates:
            if candidate.exists():
                return str(candidate)
        
        raise FileNotFoundError(
            "config.yml not found. Please specify config_path or create config.yml"
        )
    
    def _load_config(self) -> dict:
        """Load YAML configuration file."""
        print(f"Loading config from: {self.config_path}")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        
        return config
    
    def _get_db_config(self) -> dict:
        """Extract database configuration from shared SUPABASE_ENV_FILE."""
        resolved = self._resolve_runtime_config()
        hints = resolved.db_hints
        return {
            "host": hints.host,
            "port": hints.port,
            "user": hints.username or resolved.shared.postgres_user,
            "password": resolved.shared.postgres_password,
            "database": hints.database,
            "sslmode": hints.sslmode,
        }

    def _resolve_runtime_config(self) -> ResolvedRuntimeConfig:
        discovered_env = find_dotenv(usecwd=True)
        env_file_path = Path(discovered_env).resolve() if discovered_env else None
        return ConfigProvider(
            environ=os.environ,
            env_file_path=env_file_path,
            current_file=str(Path(__file__).resolve()),
            require_postgres_password=True,
        ).resolve()
    
    def _create_connection(self, name: Optional[str] = None):
        """Create a new database connection."""
        if _pg_driver == "psycopg2":
            conn = self._database_service.connect(profile_name="app")
            if name and name != self.db_config.get("database", "fabdis"):
                conn.close()
                return psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=name,
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    sslmode=self.db_config.get("sslmode", "prefer")
                )
            return conn
        else:  # pg8000
            return pg8000.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=name if name else self.db_config.get("database", "fabdis"),
                user=self.db_config["user"],
                password=self.db_config["password"],
                ssl_context=True if self.db_config.get("sslmode") != "disable" else None
            )

    @contextmanager
    def get_connection(self, name: Optional[str] = None):
        """Context manager for database connections.
        
        Yields:
            Database connection object
            
        Example:
            with db_handler.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        conn = self._create_connection(name)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """Context manager for database cursor.
        
        Args:
            cursor_factory: Optional cursor factory for special cursor types
            
        Yields:
            Database cursor object
            
        Example:
            with db_handler.get_cursor() as cur:
                cur.execute("SELECT * FROM table WHERE id = %s", (1,))
                result = cur.fetchone()
        """
        with self.get_connection() as conn:
            if _pg_driver == "psycopg2" and cursor_factory:
                cursor = conn.cursor(cursor_factory=cursor_factory)
            else:
                cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Optional tuple of query parameters
            
        Returns:
            List of result tuples
            
        Example:
            results = db_handler.execute_query(
                "SELECT * FROM users WHERE age > %s", (18,)
            )
        """
        with self.get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()
    
    def execute_dict_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results as dictionaries.
        
        Args:
            query: SQL query string
            params: Optional tuple of query parameters
            
        Returns:
            List of result dictionaries with column names as keys
            
        Example:
            results = db_handler.execute_dict_query(
                "SELECT id, name FROM users WHERE age > %s", (18,)
            )
            # Returns: [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        """
        if _pg_driver == "psycopg2":
            cursor_factory = psycopg2.extras.RealDictCursor
        else:
            cursor_factory = None
        
        with self.get_cursor(cursor_factory=cursor_factory) as cur:
            cur.execute(query, params or ())
            
            if cur.description is None:
                return []
            
            if _pg_driver == "psycopg2":
                return [dict(row) for row in cur.fetchall()]
            else:
                # For pg8000, manually create dicts from column names
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Optional tuple of query parameters
            
        Returns:
            Number of rows affected
            
        Example:
            rows_affected = db_handler.execute_update(
                "UPDATE users SET active = %s WHERE id = %s", (True, 1)
            )
        """
        with self.get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.rowcount
    
    def test_connection(self) -> bool:
        """Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result[0] == 1
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get column information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column info dictionaries
        """
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_dict_query(query, (table_name,))


