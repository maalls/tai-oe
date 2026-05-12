"""Action management API handlers."""

from typing import Dict, Any, Optional, List
from src.repository.action_repository import ActionRepository
from src.service.action_scheduler import ActionScheduler


class ActionHandlers:
    """Handler for action-related API endpoints."""
    
    def __init__(self):
        self.action_repo = ActionRepository()
        self.scheduler = ActionScheduler()
    
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
            actions = self.action_repo.list_actions(opportunity_id)
            
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
            # Validate required fields
            required_fields = ['opportunity_id', 'action_type', 'schedule_type']
            for field in required_fields:
                if field not in data:
                    return {
                        "status": "error",
                        "error_code": "MISSING_FIELD",
                        "message": f"Missing required field: {field}"
                    }
            
            # Create action
            action = self.action_repo.create_action(
                user_id=user_id,
                opportunity_id=data['opportunity_id'],
                action_type=data['action_type'],
                schedule_type=data['schedule_type'],
                schedule_config=data.get('schedule_config', {}),
                config=data.get('config', {}),
                max_executions=data.get('max_executions')
            )
            
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
            action = self.action_repo.get_action(action_id)
            
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
            # Check if action exists
            action = self.action_repo.get_action(action_id)
            if not action:
                return {
                    "status": "error",
                    "error_code": "NOT_FOUND",
                    "message": f"Action {action_id} not found"
                }
            
            # Update action
            updated_action = self.action_repo.update_action(action_id, data)
            
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
            # Check if action exists
            action = self.action_repo.get_action(action_id)
            if not action:
                return {
                    "status": "error",
                    "error_code": "NOT_FOUND",
                    "message": f"Action {action_id} not found"
                }
            
            # Delete action
            self.action_repo.delete_action(action_id)
            
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
            action = self.action_repo.pause_action(action_id)
            
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
            action = self.action_repo.resume_action(action_id)
            
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
            result = self.scheduler.execute_manually(action_id)
            
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
            logs = self.action_repo.get_execution_logs(action_id, limit=limit)
            
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
