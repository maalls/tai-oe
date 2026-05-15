"""Action management API handlers."""

from typing import Dict, Any, Optional

from src.api.routes.helpers.server_auth_helpers import require_auth, require_auth_user_id
from src.api.routes.helpers.server_body_helpers import read_json_or_error
from src.api.routes.helpers.server_query_helpers import get_qs_int
from src.api.routes.helpers.server_status_helpers import status_from_result
from src.service.action.service import ActionService


class ActionHandlers:
    """Handler for action-related API endpoints."""
    
    def __init__(self, action_service: Optional[ActionService] = None):
        self.action_service = action_service or ActionService()
    
    def handle_list_actions(self, opportunity_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List all actions for an opportunity.
        
        Args:
            opportunity_id: UUID of the opportunity
            user_id: UUID of the authenticated user (for auth check)
        
        Returns:
            {
                "status": "ok",
                "actions": [...]
            }
        """
        try:
            actions = self.action_service.list_actions(opportunity_id, user_id=user_id)
            
            return {
                "status": "ok",
                "actions": actions
            }
        except Exception as e:
            print(f"[ActionHandlers] Error listing actions: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "LIST_ACTIONS_ERROR",
                "message": str(e)
            }
    
    def handle_create_action(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a new action.
        
        Args:
            data: {
                "opportunity_id": "uuid",
                "action_type": "recurring_quote",
                "schedule_type": "monthly",
                "schedule_config": {...},
                "config": {...},
                "max_executions": 12
            }
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok",
                "action": {...}
            }
        """
        try:
            action = self.action_service.create_action(data, user_id=user_id)
            
            if not action:
                return {
                    "status": "error",
                    "error_code": "CREATE_FAILED",
                    "message": "Failed to create action"
                }
            
            return {
                "status": "ok",
                "action": action
            }
        except ValueError as e:
            if str(e).startswith("Missing required field:"):
                return {
                    "status": "error",
                    "error_code": "MISSING_FIELD",
                    "message": str(e),
                }
            return {
                "status": "error",
                "error_code": "CREATE_ACTION_ERROR",
                "message": str(e),
            }
        except Exception as e:
            print(f"[ActionHandlers] Error creating action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "CREATE_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_get_action(self, action_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a single action by ID.
        
        Args:
            action_id: UUID of the action
            user_id: UUID of the authenticated user (for auth check)
        
        Returns:
            {
                "status": "ok",
                "action": {...}
            }
        """
        try:
            action = self.action_service.get_action(action_id, user_id=user_id)
            
            if not action:
                return {
                    "status": "error",
                    "error_code": "NOT_FOUND",
                    "message": f"Action {action_id} not found"
                }
            
            return {
                "status": "ok",
                "action": action
            }
        except Exception as e:
            print(f"[ActionHandlers] Error getting action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "GET_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_update_action(self, action_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Update an action.
        
        Args:
            action_id: UUID of the action
            data: Fields to update
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok",
                "action": {...}
            }
        """
        try:
            updated_action = self.action_service.update_action(action_id, data, user_id=user_id)
            if not updated_action:
                return {
                    "status": "error",
                    "error_code": "NOT_FOUND",
                    "message": f"Action {action_id} not found"
                }

            if not updated_action:
                return {
                    "status": "error",
                    "error_code": "UPDATE_FAILED",
                    "message": "Failed to update action"
                }
            
            return {
                "status": "ok",
                "action": updated_action
            }
        except Exception as e:
            print(f"[ActionHandlers] Error updating action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "UPDATE_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_delete_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete an action.
        
        Args:
            action_id: UUID of the action
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok"
            }
        """
        try:
            deleted = self.action_service.delete_action(action_id, user_id=user_id)
            if not deleted:
                return {
                    "status": "error",
                    "error_code": "NOT_FOUND",
                    "message": f"Action {action_id} not found"
                }
            
            return {
                "status": "ok",
                "message": f"Action {action_id} deleted"
            }
        except Exception as e:
            print(f"[ActionHandlers] Error deleting action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "DELETE_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_pause_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """
        Pause an action.
        
        Args:
            action_id: UUID of the action
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok",
                "action": {...}
            }
        """
        try:
            action = self.action_service.pause_action(action_id, user_id=user_id)
            
            if not action:
                return {
                    "status": "error",
                    "error_code": "PAUSE_FAILED",
                    "message": "Failed to pause action"
                }
            
            return {
                "status": "ok",
                "action": action
            }
        except Exception as e:
            print(f"[ActionHandlers] Error pausing action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "PAUSE_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_resume_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """
        Resume a paused action.
        
        Args:
            action_id: UUID of the action
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok",
                "action": {...}
            }
        """
        try:
            action = self.action_service.resume_action(action_id, user_id=user_id)
            
            if not action:
                return {
                    "status": "error",
                    "error_code": "RESUME_FAILED",
                    "message": "Failed to resume action"
                }
            
            return {
                "status": "ok",
                "action": action
            }
        except Exception as e:
            print(f"[ActionHandlers] Error resuming action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "RESUME_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_execute_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """
        Manually execute an action.
        
        Args:
            action_id: UUID of the action
            user_id: UUID of the authenticated user
        
        Returns:
            {
                "status": "ok",
                "execution": {
                    "action_id": "...",
                    "status": "success",
                    "duration_ms": 123,
                    "result": {...}
                }
            }
        """
        try:
            result = self.action_service.execute_action(action_id, user_id=user_id)
            
            return {
                "status": "ok",
                "execution": result
            }
        except Exception as e:
            print(f"[ActionHandlers] Error executing action: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "EXECUTE_ACTION_ERROR",
                "message": str(e)
            }
    
    def handle_get_action_logs(self, action_id: str, limit: int = 50, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get execution logs for an action.
        
        Args:
            action_id: UUID of the action
            limit: Maximum number of logs to return
            user_id: UUID of the authenticated user (for auth check)
        
        Returns:
            {
                "status": "ok",
                "logs": [...]
            }
        """
        try:
            logs = self.action_service.get_action_logs(action_id, limit=limit, user_id=user_id)
            
            return {
                "status": "ok",
                "logs": logs
            }
        except Exception as e:
            print(f"[ActionHandlers] Error getting action logs: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_code": "GET_LOGS_ERROR",
                "message": str(e)
            }


def handle_actions_create_post(handler):
    """Handle /api/actions POST endpoint."""
    data = read_json_or_error(handler)
    if data is None:
        return None

    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_create_action(data, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_pause_post(handler, pause_action_match):
    """Handle /api/actions/{id}/pause POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    action_id = pause_action_match.group(1)

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_pause_action(action_id, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_resume_post(handler, resume_action_match):
    """Handle /api/actions/{id}/resume POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    action_id = resume_action_match.group(1)

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_resume_action(action_id, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_execute_post(handler, execute_action_match):
    """Handle /api/actions/{id}/execute POST endpoint."""
    user_data = require_auth(handler)
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    action_id = execute_action_match.group(1)

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_execute_action(action_id, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_delete(handler, action_delete_match):
    """Handle DELETE /api/actions/{id}."""
    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None

    action_id = action_delete_match.group(1)

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_delete_action(action_id=action_id, user_id=user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_opportunity_actions_list_get(handler, opportunity_id: str):
    """Handle /api/opportunities/<id>/actions GET endpoint."""
    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None
    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_list_actions(opportunity_id, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_get(handler, action_id: str):
    """Handle /api/actions/<id> GET endpoint."""
    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None
    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_get_action(action_id, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_logs_get(handler, action_id: str, qs):
    """Handle /api/actions/<id>/logs GET endpoint."""
    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None
    request_handlers = handler.request_handlers
    limit = get_qs_int(qs, 'limit', 50)
    result = request_handlers.action_handlers.handle_get_action_logs(action_id, limit, user_id)
    status = status_from_result(result)
    return handler.json(result, status)


def handle_action_update_put(handler, update_action_match):
    """Handle PUT /api/actions/{id}."""
    data = read_json_or_error(handler)
    if data is None:
        return None

    user_id = require_auth_user_id(handler)
    if user_id is None:
        return None

    action_id = update_action_match.group(1)

    request_handlers = handler.request_handlers
    result = request_handlers.action_handlers.handle_update_action(action_id, data, user_id)
    status = status_from_result(result)
    return handler.json(result, status)
