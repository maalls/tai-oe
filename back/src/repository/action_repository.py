"""Repository for action CRUD operations and scheduling."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID
import json

from src.infrastructure.clients.supabase import get_supabase_service


class ActionRepository:
    """Handle database operations for actions."""
    
    def __init__(self):
        self.supabase = get_supabase_service()
    
    def create_action(self, user_id: str, opportunity_id: str, action_type: str,
                     schedule_type: str, schedule_config: Dict[str, Any],
                     config: Dict[str, Any], max_executions: Optional[int] = None) -> Dict[str, Any]:
        """Create a new action."""
        next_execution = self._calculate_next_execution(schedule_type, schedule_config)
        
        data = {
            'user_id': user_id,
            'opportunity_id': opportunity_id,
            'action_type': action_type,
            'status': 'active',
            'schedule_type': schedule_type,
            'schedule_config': schedule_config,
            'config': config,
            'next_execution_at': next_execution.isoformat() if next_execution else None,
            'execution_count': 0,
            'max_executions': max_executions,
            'created_by': user_id,
        }
        
        response = self.supabase.table('action').insert(data).execute()
        return response.data[0] if response.data else None
    
    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get a single action by ID."""
        response = self.supabase.table('action').select('*').eq('id', action_id).single().execute()
        return response.data if response.data else None
    
    def list_actions(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """List all actions for an opportunity."""
        response = self.supabase.table('action').select('*').eq('opportunity_id', opportunity_id).execute()
        return response.data if response.data else []
    
    def update_action(self, action_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an action."""
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        response = self.supabase.table('action').update(updates).eq('id', action_id).execute()
        return response.data[0] if response.data else None
    
    def delete_action(self, action_id: str) -> bool:
        """Delete an action."""
        response = self.supabase.table('action').delete().eq('id', action_id).execute()
        return True
    
    def get_due_actions(self) -> List[Dict[str, Any]]:
        """Get all actions that are due for execution."""
        now = datetime.now(timezone.utc).isoformat()
        response = self.supabase.table('action').select('*')\
            .eq('status', 'active')\
            .lte('next_execution_at', now)\
            .execute()
        return response.data if response.data else []
    
    def record_execution(self, action_id: str, status: str, duration_ms: int = None,
                        result_data: Dict[str, Any] = None, error_message: str = None) -> Dict[str, Any]:
        """Record an action execution."""
        log_data = {
            'action_id': action_id,
            'status': status,
            'executed_at': datetime.now(timezone.utc).isoformat(),
            'duration_ms': duration_ms,
            'result_data': result_data,
            'error_message': error_message,
        }
        
        response = self.supabase.table('action_execution_log').insert(log_data).execute()
        
        # Update action execution count and last executed time
        action = self.get_action(action_id)
        if action:
            updates = {
                'last_executed_at': datetime.now(timezone.utc).isoformat(),
                'execution_count': (action.get('execution_count', 0) or 0) + 1,
            }
            
            # If max executions reached, mark as completed
            if action.get('max_executions') and updates['execution_count'] >= action['max_executions']:
                updates['status'] = 'completed'
            
            self.update_action(action_id, updates)
        
        return response.data[0] if response.data else None
    
    def get_execution_logs(self, action_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution logs for an action."""
        response = self.supabase.table('action_execution_log').select('*')\
            .eq('action_id', action_id)\
            .order('executed_at', desc=True)\
            .limit(limit)\
            .execute()
        return response.data if response.data else []
    
    def pause_action(self, action_id: str) -> Dict[str, Any]:
        """Pause an action."""
        return self.update_action(action_id, {'status': 'paused'})
    
    def resume_action(self, action_id: str) -> Dict[str, Any]:
        """Resume a paused action."""
        action = self.get_action(action_id)
        if action:
            next_execution = self._calculate_next_execution(
                action['schedule_type'],
                action['schedule_config']
            )
            return self.update_action(action_id, {
                'status': 'active',
                'next_execution_at': next_execution.isoformat() if next_execution else None,
            })
        return None
    
    def _calculate_next_execution(self, schedule_type: str, schedule_config: Dict[str, Any]) -> Optional[datetime]:
        """Calculate next execution time based on schedule."""
        now = datetime.now(timezone.utc)
        
        if schedule_type == 'monthly':
            day = schedule_config.get('day_of_month', 1)
            time_str = schedule_config.get('time', '09:00')
            
            # Parse time
            hour, minute = map(int, time_str.split(':'))
            
            # Get next month's scheduled date
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            # Handle "last day of month"
            if day == 'last' or day > 28:
                import calendar
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                next_date = next_month.replace(day=last_day, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_date = next_month.replace(day=min(day, 28), hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_date if next_date > now else next_date + timedelta(days=30)
        
        elif schedule_type == 'weekly':
            day_of_week = schedule_config.get('day_of_week', 0)
            time_str = schedule_config.get('time', '09:00')
            
            hour, minute = map(int, time_str.split(':'))
            
            # Find next occurrence of day
            days_ahead = (day_of_week - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            
            next_date = now + timedelta(days=days_ahead)
            next_date = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_date if next_date > now else next_date + timedelta(weeks=1)
        
        elif schedule_type == 'daily':
            time_str = schedule_config.get('time', '09:00')
            hour, minute = map(int, time_str.split(':'))
            
            next_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_date <= now:
                next_date += timedelta(days=1)
            
            return next_date
        
        elif schedule_type == 'one_time':
            # One-time actions execute immediately or at specified time
            return now
        
        return None
