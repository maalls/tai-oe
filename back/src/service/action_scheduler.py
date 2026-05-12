"""Background scheduler for executing due actions."""

import time
from datetime import datetime, timezone
from src.repository.action_repository import ActionRepository
from src.service.action_executor import ActionExecutor


class ActionScheduler:
    """Background scheduler for actions."""
    
    def __init__(self, check_interval_seconds: int = 60):
        self.action_repo = ActionRepository()
        self.executor = ActionExecutor()
        self.check_interval = check_interval_seconds
        self.running = False
    
    def start(self):
        """Start the scheduler loop."""
        self.running = True
        print("[ActionScheduler] Starting action scheduler")
        
        while self.running:
            try:
                self._check_and_execute()
            except Exception as e:
                print(f"[ActionScheduler] Error in scheduler loop: {e}")
                import traceback
                traceback.print_exc()
            
            # Sleep before next check
            time.sleep(self.check_interval)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        print("[ActionScheduler] Stopping action scheduler")
    
    def _check_and_execute(self):
        """Check for due actions and execute them."""
        try:
            due_actions = self.action_repo.get_due_actions()
            
            if due_actions:
                print(f"[ActionScheduler] Found {len(due_actions)} due actions")
                
                for action in due_actions:
                    self._execute_action(action)
        
        except Exception as e:
            print(f"[ActionScheduler] Error checking due actions: {e}")
            import traceback
            traceback.print_exc()
    
    def _execute_action(self, action: dict):
        """Execute a single action."""
        action_id = action['id']
        print(f"[ActionScheduler] Executing action {action_id} (type: {action['action_type']})")
        
        try:
            result = self.executor.execute(action)
            print(f"[ActionScheduler] Action {action_id} completed: {result['status']}")
        
        except Exception as e:
            print(f"[ActionScheduler] Failed to execute action {action_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def execute_manually(self, action_id: str) -> dict:
        """Manually trigger execution of a specific action."""
        action = self.action_repo.get_action(action_id)
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        print(f"[ActionScheduler] Manually triggering action {action_id}")
        return self.executor.execute(action)
