# Dependency Injection Refactoring Guide

## Current Architecture Issues

Your code currently has **tight coupling** between classes:

1. **Classes instantiate their own dependencies** (e.g., `RequestHandlers` creates `CsvHandlers`, `DatabaseHandlers`, etc.)
2. **Direct imports of concrete classes** throughout the codebase
3. **Shared class variables** in HTTP handlers (`_embedding_generator`, `_csv_reader`, etc.) make testing difficult
4. **Supabase clients use global singletons** which can't be mocked for tests
5. **Hard to test** because you can't inject mock implementations

## Proposed Architecture

### 1. **Create Interfaces (Abstract Base Classes)**

```python
# src/core/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

class IFileHandler(ABC):
    """Interface for file operations."""
    @abstractmethod
    def list_sources(self) -> List[str]:
        pass

    @abstractmethod
    def list_files_for_source(self, source: str) -> List[str]:
        pass

class IDatabaseHandler(ABC):
    """Interface for database operations."""
    @abstractmethod
    def execute_dict_query(self, query: str) -> List[Dict]:
        pass

class IQdrantHandler(ABC):
    """Interface for vector database operations."""
    @abstractmethod
    def get_collections(self) -> List[str]:
        pass

class IEmbeddingGenerator(ABC):
    """Interface for embeddings."""
    @abstractmethod
    def generate(self, text: str) -> List[float]:
        pass

class ICsvReader(ABC):
    """Interface for CSV reading."""
    @abstractmethod
    def read(self, file_path, offset: int = 0, limit: int = 100, filters: Optional[Dict] = None) -> Dict:
        pass
```

### 2. **Create a Dependency Container (IoC Container)**

```python
# src/core/container.py
from typing import Optional
from src.reader.csv import CSVReader
from src.embeddings import EmbeddingGenerator
from src.rag.file_handler import FileHandler
from src.rag.db_client import DatabaseHandler
from src.rag.qdrant_handler import QdrantHandler
from src.controller.auth.auth_handler import AuthHandler
from src.rag.classify_handler import ClassifyHandler

class Container:
    """Dependency injection container for managing application dependencies."""

    def __init__(self):
        self._instances = {}
        self._factories = {}

    def register_singleton(self, key: str, factory, *args, **kwargs):
        """Register a singleton dependency."""
        self._factories[key] = (factory, args, kwargs)

    def register_factory(self, key: str, factory):
        """Register a factory (creates new instance each time)."""
        self._factories[key] = (factory, (), {})

    def get(self, key: str):
        """Get or create a dependency."""
        if key in self._instances:
            return self._instances[key]

        if key not in self._factories:
            raise KeyError(f"Dependency '{key}' not registered")

        factory, args, kwargs = self._factories[key]
        instance = factory(*args, **kwargs)

        # Cache as singleton if it was registered as one
        if key in self._instances:
            self._instances[key] = instance

        return instance

def create_container(config: Dict) -> Container:
    """Factory function to create and configure the DI container."""
    container = Container()

    # Register singletons
    container.register_singleton('config', lambda: config)

    container.register_singleton(
        'csv_reader',
        CSVReader,
        config['STORAGE_DIR']
    )

    container.register_singleton(
        'embedding_generator',
        EmbeddingGenerator
    )

    container.register_singleton(
        'file_handler',
        FileHandler,
        config['STORAGE_DIR'],
        container.get('csv_reader')
    )

    container.register_singleton(
        'db_handler',
        DatabaseHandler
    )

    container.register_singleton(
        'qdrant_handler',
        QdrantHandler
    )

    container.register_singleton(
        'auth_handler',
        AuthHandler
    )

    container.register_singleton(
        'classify_handler',
        ClassifyHandler
    )

    # Register composite handlers with dependencies
    container.register_singleton(
        'request_handlers',
        lambda: RequestHandlers(
            file_handler=container.get('file_handler'),
            db_handler=container.get('db_handler'),
            qdrant_handler=container.get('qdrant_handler')
        )
    )

    return container
```

### 3. **Refactor the HTTP Handler**

**Before (tightly coupled):**

```python
class Rag(http.server.SimpleHTTPRequestHandler):
    _embedding_generator = None
    _csv_reader = None

    @classmethod
    def init_resources(cls, config):
        cls._embedding_generator = EmbeddingGenerator()
        cls._csv_reader = CSVReader(config['STORAGE_DIR'])
```

**After (dependency injection):**

```python
class Rag(http.server.SimpleHTTPRequestHandler):
    # Class-level DI container
    _container: Optional[Container] = None

    @classmethod
    def set_container(cls, container: Container):
        """Inject the DI container."""
        cls._container = container

    def do_GET(self):
        """Handle GET requests with injected dependencies."""
        request_handlers = self._container.get('request_handlers')
        # ... use request_handlers

    @property
    def embedding_generator(self):
        """Property for lazy access to injected dependency."""
        return self._container.get('embedding_generator')

    @property
    def csv_reader(self):
        """Property for lazy access to injected dependency."""
        return self._container.get('csv_reader')
```

### 4. **Update Main Application Entry Point**

**Before:**

```python
def make_handler(config):
    class Rag(http.server.SimpleHTTPRequestHandler):
        _embedding_generator = None
        _csv_reader = None

        @classmethod
        def init_resources(cls, config):
            cls._embedding_generator = EmbeddingGenerator()
            cls._csv_reader = CSVReader(config['STORAGE_DIR'])
```

**After:**

```python
# src/main.py
from src.core.container import create_container

def create_application(config: Dict):
    """Create and configure the application with dependency injection."""
    # Create DI container and register all dependencies
    container = create_container(config)

    # Create HTTP handler factory
    def make_handler():
        class Rag(http.server.SimpleHTTPRequestHandler):
            _container = container

            def do_GET(self):
                """Handle GET requests."""
                request_handlers = self._container.get('request_handlers')
                # Route and handle request
                # ...

    return make_handler, container

if __name__ == '__main__':
    config = {
        "PORT": int(os.environ.get("PORT", "8088")),
        "STORAGE_DIR": Path(os.environ.get("STORAGE_DIR", "var/storage")).resolve(),
    }

    make_handler, container = create_application(config)
    server = ThreadingHTTPServer(("localhost", config["PORT"]), make_handler())
    server.serve_forever()
```

### 5. **Fix Supabase Client (Replace Globals)**

**Before:**

```python
_supabase_anon: Client = None

def get_supabase_anon() -> Client:
    global _supabase_anon
    if _supabase_anon is None:
        _supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase_anon
```

**After:**

```python
# src/supabase/supabase_client.py
class SupabaseClientFactory:
    """Factory for creating Supabase clients with DI support."""

    def __init__(self, url: str, anon_key: str, service_key: str):
        self.url = url
        self.anon_key = anon_key
        self.service_key = service_key
        self._anon_client = None
        self._service_client = None

    def get_anon(self) -> Client:
        """Get or create anon client."""
        if self._anon_client is None:
            self._anon_client = create_client(self.url, self.anon_key)
        return self._anon_client

    def get_service(self) -> Client:
        """Get or create service client."""
        if self._service_client is None:
            self._service_client = create_client(self.url, self.service_key)
        return self._service_client

# Register in container:
container.register_singleton(
    'supabase_factory',
    SupabaseClientFactory,
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY'),
    os.getenv('SUPABASE_SERVICE_KEY')
)
```

## Benefits

| Aspect            | Before                                   | After                                              |
| ----------------- | ---------------------------------------- | -------------------------------------------------- |
| **Testing**       | Hard to mock dependencies                | Easy to inject test mocks                          |
| **Coupling**      | Tight coupling between classes           | Loose coupling via interfaces                      |
| **Reusability**   | Classes tied to specific implementations | Components reusable with different implementations |
| **Configuration** | Config scattered throughout              | Centralized in container                           |
| **Maintenance**   | Changes break multiple files             | Changes isolated to container                      |
| **Clarity**       | Dependencies implicit                    | Dependencies explicit in constructor               |

## Implementation Steps

1. **Create interfaces** in `src/core/interfaces.py`
2. **Create container** in `src/core/container.py`
3. **Update handlers** to accept dependencies in `__init__`
4. **Update main entry point** (`rag.py`) to use container
5. **Replace global singletons** (Supabase) with container-managed instances
6. **Write tests** using mock objects injected via container

## Testing Example

```python
# tests/test_request_handlers.py
import pytest
from unittest.mock import Mock
from src.rag.handlers import RequestHandlers

@pytest.fixture
def mock_file_handler():
    handler = Mock()
    handler.list_sources.return_value = ['test_source']
    return handler

@pytest.fixture
def mock_db_handler():
    return Mock()

@pytest.fixture
def request_handlers(mock_file_handler, mock_db_handler):
    return RequestHandlers(
        file_handler=mock_file_handler,
        db_handler=mock_db_handler
    )

def test_handle_sources(request_handlers, mock_file_handler):
    result = request_handlers.handle_sources()
    assert result == ['test_source']
    mock_file_handler.list_sources.assert_called_once()
```

## Priority for Implementation

1. **High** (Start here):
   - Create container and interfaces
   - Update `RequestHandlers` and sub-handlers
   - Update main HTTP handler

2. **Medium** (Quick wins):
   - Replace Supabase global singletons
   - Add interface classes to handlers

3. **Low** (Nice to have):
   - Add full test suite with DI
   - Create factory patterns for complex objects
