"""Central role-to-route access policy for API authorization."""

from __future__ import annotations

from typing import Final

_ACCESS_POLICY: Final[dict[str, set[str]]] = {
    "/api/admin/users": {"admin"},
    "/api/admin/users/{target_user_id}/role": {"admin"},
    "/api/csv/sources": {"admin"},
    "/api/csv/files": {"admin"},
    "/api/csv/preview": {"admin"},
    "/api/csv/source": {"admin"},
    "/api/csv/raw": {"admin"},
    "/api/csv/download": {"admin"},
    "/api/csv/query": {"admin"},
    "/api/email-fetch-loop/status": {"admin"},
    "/api/fetch": {"admin"},
    "/api/curl": {"admin"},
    "/api/fs/create": {"admin"},
    "/api/fs/read": {"admin"},
    "/api/prompt/{relative_path:path}": {"admin"},
    "/api/storage/{raw_filename:path}": {"admin", "user"},
    "/api/opportunities/{opportunity_id}/actions": {"admin"},
    "/api/opportunity/{opportunity_id}/source": {"admin"},
    "/api/opportunity": {"admin"},
    "/api/opportunity/{opportunity_id}/stage-history": {"admin"},
    "/api/opportunity/{opportunity_id}/stage-state": {"admin"},
    "/api/opportunity/advance": {"admin"},
    "/api/opportunities/search": {"admin"},
    "/api/opportunities/create-manual": {"admin"},
    "/api/opportunities/create-draft": {"admin"},
    "/api/opportunity/{opportunity_id}/name": {"admin"},
    "/api/opportunity/{opportunity_id}/account": {"admin"},
    "/api/opportunity/{opportunity_id}/extract-author-contact": {"admin"},
    "/api/opportunities/create-from-email": {"admin"},
    "/api/opportunities/{opportunity_ids}": {"admin"},
    "/api/opportunity/{opportunity_id}/rfq/generate": {"admin"},
    "/api/opportunity/{opportunity_id}/rfq/create-from-text": {"admin"},
    "/api/opportunity/{opportunity_id}/send-quote": {"admin"},
    "/api/opportunity/{opportunity_id}/sent-email": {"admin"},
    "/api/actions": {"admin"},
    "/api/actions/{action_id}": {"admin"},
    "/api/actions/{action_id}/pause": {"admin"},
    "/api/actions/{action_id}/resume": {"admin"},
    "/api/action/{action_id}/execute": {"admin"},
    "/api/actions/{action_id}/execute": {"admin"},
    "/api/actions/{action_id}/logs": {"admin"},
    "/api/document/{document_id}/status": {"admin"},
    "/api/document/{document_id}/storage-key": {"admin"},
    "/api/document/extract-rfp": {"admin"},
    "/api/document/update-content": {"admin"},
    "DELETE /api/document/{document_id}": {"admin"},
    "/api/chat/attachments": {"admin"},
}


def allowed_roles_for_route(route_path: str, method: str | None = None) -> set[str]:
    """Return allowed roles for a route path; empty set means deny by default."""
    if method:
        method_key = f"{method.upper()} {route_path}"
        if method_key in _ACCESS_POLICY:
            return set(_ACCESS_POLICY.get(method_key, set()))

    return set(_ACCESS_POLICY.get(route_path, set()))


def can_access_route(role: str | None, route_path: str, method: str | None = None) -> bool:
    """Return True when role is allowed for the given route path."""
    if not role:
        return False

    return role in allowed_roles_for_route(route_path, method=method)
