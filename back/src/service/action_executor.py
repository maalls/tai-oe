"""Action executor for running different types of actions."""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import time
from src.repository.action_repository import ActionRepository


class ActionExecutor:
    """Execute different types of actions."""
    
    def __init__(self):
        self.action_repo = ActionRepository()
    
    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action and record the result."""
        action_id = action['id']
        action_type = action['action_type']
        
        start_time = time.time()
        result = None
        error = None
        status = 'success'
        
        try:
            if action_type == 'recurring_quote':
                result = self._execute_recurring_quote(action)
            elif action_type == 'recurring_invoice':
                result = self._execute_recurring_invoice(action)
            elif action_type == 'follow_up_email':
                result = self._execute_follow_up_email(action)
            elif action_type == 'stage_reminder':
                result = self._execute_stage_reminder(action)
            else:
                raise ValueError(f"Unknown action type: {action_type}")
        
        except Exception as e:
            status = 'failed'
            error = str(e)
            print(f"[ActionExecutor] Error executing action {action_id}: {error}")
            import traceback
            traceback.print_exc()
        
        # Record execution
        duration_ms = int((time.time() - start_time) * 1000)
        self.action_repo.record_execution(
            action_id=action_id,
            status=status,
            duration_ms=duration_ms,
            result_data=result,
            error_message=error
        )
        
        # Calculate next execution if action is still active
        action = self.action_repo.get_action(action_id)
        if action and action.get('status') == 'active':
            next_execution = self.action_repo._calculate_next_execution(
                action['schedule_type'],
                action['schedule_config']
            )
            if next_execution:
                self.action_repo.update_action(action_id, {
                    'next_execution_at': next_execution.isoformat()
                })
        
        return {
            'action_id': action_id,
            'status': status,
            'duration_ms': duration_ms,
            'result': result,
            'error': error
        }
    
    def _execute_recurring_quote(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a recurring quote."""
        config = action['config']
        opportunity_id = action['opportunity_id']
        
        # This is a placeholder - actual implementation would:
        # 1. Load base quote document
        # 2. Create new quote with same structure
        # 3. Save new quote
        # 4. Generate PDF if needed
        # 5. Auto-send if configured
        
        print(f"[ActionExecutor] Executing recurring quote for opportunity {opportunity_id}")
        
        return {
            'quote_id': f'quote-{datetime.now().timestamp()}',
            'sent': config.get('auto_send', False),
            'message': 'Recurring quote execution placeholder'
        }
    
    def _execute_recurring_invoice(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a recurring invoice."""
        config = action['config']
        opportunity_id = action['opportunity_id']
        
        # Placeholder implementation
        print(f"[ActionExecutor] Executing recurring invoice for opportunity {opportunity_id}")
        
        return {
            'invoice_id': f'invoice-{datetime.now().timestamp()}',
            'amount': config.get('amount'),
            'sent': config.get('auto_send', False),
            'message': 'Recurring invoice execution placeholder'
        }
    
    def _execute_follow_up_email(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Send a follow-up email."""
        config = action['config']
        opportunity_id = action['opportunity_id']
        
        # Placeholder implementation
        print(f"[ActionExecutor] Executing follow-up email for opportunity {opportunity_id}")
        
        return {
            'email_sent': True,
            'recipients': config.get('recipients', []),
            'message': 'Follow-up email execution placeholder'
        }
    
    def _execute_stage_reminder(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Send stage reminder notification."""
        config = action['config']
        opportunity_id = action['opportunity_id']
        
        # Placeholder implementation
        print(f"[ActionExecutor] Executing stage reminder for opportunity {opportunity_id}")
        
        return {
            'notified_users': config.get('notify_users', []),
            'stage': config.get('stage'),
            'message': 'Stage reminder execution placeholder'
        }
