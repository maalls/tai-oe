"""FastAPI action router."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api.authz.route_access import AccessContext, build_default_access_context_dependency
from src.api.common.responses import error_response
from src.api.dependencies import get_action_service
from src.service.action.service import ActionService

router = APIRouter(tags=["action"])

_action_access = build_default_access_context_dependency()


@router.get("/api/opportunities/{opportunity_id}/actions")
def list_actions(
    opportunity_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        actions = action_service.list_actions(opportunity_id, user_id=requester_id)
        return JSONResponse({"status": "ok", "actions": actions}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "LIST_ACTIONS_ERROR")


@router.post("/api/actions")
def create_action(
    payload: dict[str, Any],
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        action = action_service.create_action(payload, user_id=requester_id)
        if not action:
            return error_response("Failed to create action", "CREATE_FAILED")
        return JSONResponse({"status": "ok", "action": action}, status_code=200)
    except ValueError as exc:
        error_code = "MISSING_FIELD" if str(exc).startswith("Missing required field:") else "CREATE_ACTION_ERROR"
        return error_response(str(exc), error_code)
    except Exception as exc:
        return error_response(str(exc), "CREATE_ACTION_ERROR")


@router.get("/api/actions/{action_id}")
def get_action(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        action = action_service.get_action(action_id, user_id=requester_id)
        if not action:
            return error_response(f"Action {action_id} not found", "NOT_FOUND")
        return JSONResponse({"status": "ok", "action": action}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "GET_ACTION_ERROR")


@router.post("/api/actions/{action_id}/pause")
def pause_action(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        action = action_service.pause_action(action_id, user_id=requester_id)
        if not action:
            return error_response(f"Action {action_id} not found", "NOT_FOUND")
        return JSONResponse({"status": "ok", "action": action}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "PAUSE_ACTION_ERROR")


@router.post("/api/actions/{action_id}/resume")
def resume_action(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        action = action_service.resume_action(action_id, user_id=requester_id)
        if not action:
            return error_response(f"Action {action_id} not found", "NOT_FOUND")
        return JSONResponse({"status": "ok", "action": action}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "RESUME_ACTION_ERROR")


def _execute_action_response(action_id: str, user_id: str, action_service: ActionService) -> JSONResponse:
    try:
        result = action_service.execute_action(action_id, user_id=user_id)
        status_code = 400 if result.get("status") == "error" else 200
        return JSONResponse(result, status_code=status_code)
    except Exception as exc:
        return error_response(str(exc), "EXECUTE_ACTION_ERROR")


@router.post("/api/action/{action_id}/execute")
def execute_action_frontend(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()
    return _execute_action_response(action_id, requester_id, action_service)


@router.post("/api/actions/{action_id}/execute")
def execute_action_legacy_alias(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()
    return _execute_action_response(action_id, requester_id, action_service)


@router.get("/api/actions/{action_id}/logs")
def get_action_logs(
    action_id: str,
    limit: int = Query(default=50),
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        logs = action_service.get_action_logs(action_id, limit=limit, user_id=requester_id)
        return JSONResponse({"status": "ok", "logs": logs}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "GET_ACTION_LOGS_ERROR")


@router.put("/api/actions/{action_id}")
def update_action(
    action_id: str,
    payload: dict[str, Any],
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        action = action_service.update_action(action_id, payload, user_id=requester_id)
        if not action:
            return error_response(f"Action {action_id} not found", "NOT_FOUND")
        return JSONResponse({"status": "ok", "action": action}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "UPDATE_ACTION_ERROR")


@router.delete("/api/actions/{action_id}")
def delete_action(
    action_id: str,
    requester: AccessContext = Depends(_action_access),
    action_service: ActionService = Depends(get_action_service),
):
    requester_id = requester.get_user_id()

    try:
        deleted = action_service.delete_action(action_id, user_id=requester_id)
        if not deleted:
            return error_response(f"Action {action_id} not found", "NOT_FOUND")
        return JSONResponse({"status": "ok", "message": f"Action {action_id} deleted"}, status_code=200)
    except Exception as exc:
        return error_response(str(exc), "DELETE_ACTION_ERROR")