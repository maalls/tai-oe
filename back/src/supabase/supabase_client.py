"""
Supabase client wrapper for authentication and database operations.
"""
import os
import httpx
from pathlib import Path
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from dotenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()


def _load_shared_supabase_env() -> None:
    """Load SUPABASE_* vars from shared Supabase env file when available."""
    shared_env_rel = os.getenv('SUPABASE_ENV_FILE', '../supabase/.env.prod')
    shared_env_path = Path(shared_env_rel)
    if not shared_env_path.is_absolute():
        back_dir = Path(__file__).resolve().parents[2]
        shared_env_path = (back_dir / shared_env_path).resolve()

    if not shared_env_path.exists():
        return

    values = dotenv_values(shared_env_path)
    shared_url = values.get('SUPABASE_PUBLIC_URL') or values.get('API_EXTERNAL_URL') or values.get('SITE_URL')
    if shared_url:
        os.environ['SUPABASE_URL'] = shared_url
    if values.get('ANON_KEY'):
        os.environ['SUPABASE_ANON_KEY'] = values['ANON_KEY']
    if values.get('SERVICE_ROLE_KEY'):
        os.environ['SUPABASE_SERVICE_KEY'] = values['SERVICE_ROLE_KEY']


_load_shared_supabase_env()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Anon client for frontend-like operations (respects RLS)
_supabase_anon: Client = None

# Service role client for backend operations (bypasses RLS)
_supabase_service: Client = None

# Shared HTTP client used by Supabase internals.
_supabase_httpx_client: httpx.Client = None


def _get_supabase_httpx_client() -> httpx.Client:
    global _supabase_httpx_client
    if _supabase_httpx_client is None:
        _supabase_httpx_client = httpx.Client(timeout=120.0)
    return _supabase_httpx_client


def _get_supabase_options() -> SyncClientOptions:
    return SyncClientOptions(httpx_client=_get_supabase_httpx_client())


def get_supabase_anon() -> Client:
    """
    Get the Supabase client with anon key (respects Row Level Security).
    Use this for operations that should respect RLS policies.
    """
    global _supabase_anon
    if _supabase_anon is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        _supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=_get_supabase_options())
    return _supabase_anon


def get_supabase_service() -> Client:
    """
    Get the Supabase client with service role key (bypasses Row Level Security).
    Use this for admin operations and backend tasks that need to bypass RLS.
    """
    global _supabase_service
    if _supabase_service is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        _supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY, options=_get_supabase_options())
    return _supabase_service
