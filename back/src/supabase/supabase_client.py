"""Backward-compatible shim — real implementation in src.infrastructure.clients.supabase."""

from src.infrastructure.clients.supabase import get_supabase_anon, get_supabase_service

__all__ = ["get_supabase_anon", "get_supabase_service"]
