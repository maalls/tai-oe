"""Repository for action CRUD operations and scheduling."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_service


class ActionRepository:
    """Handle database operations for actions."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = DatabaseHandler(
                database_service=create_database_service(
                    current_file=__file__,
                    require_postgres_password=True,
                )
            )
        return self.db_handler
    
    def create_action(self, user_id: str, opportunity_id: str, action_type: str,
                     schedule_type: str, schedule_config: Dict[str, Any],
                     config: Dict[str, Any], max_executions: Optional[int] = None) -> Dict[str, Any]:
        """Create a new action."""
        next_execution = self._calculate_next_execution(schedule_type, schedule_config)

        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO action (
                user_id,
                opportunity_id,
                action_type,
                status,
                schedule_type,
                schedule_config,
                config,
                next_execution_at,
                execution_count,
                max_executions,
                created_by
            ) VALUES (%s, %s, %s, 'active', %s, %s::jsonb, %s::jsonb, %s, 0, %s, %s)
            RETURNING *
            """,
            (
                user_id,
                opportunity_id,
                action_type,
                schedule_type,
                json.dumps(schedule_config or {}),
                json.dumps(config or {}),
                next_execution.isoformat() if next_execution else None,
                max_executions,
                user_id,
            ),
        )
        return rows[0] if rows else None
    
    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get a single action by ID."""
        rows = self._get_db_handler().execute_dict_query(
            "SELECT * FROM action WHERE id = %s LIMIT 1",
            (action_id,),
        )
        return rows[0] if rows else None
    
    def list_actions(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """List all actions for an opportunity."""
        return self._get_db_handler().execute_dict_query(
            "SELECT * FROM action WHERE opportunity_id = %s ORDER BY created_at DESC",
            (opportunity_id,),
        )
    
    def update_action(self, action_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an action."""
        payload = dict(updates)
        payload['updated_at'] = datetime.now(timezone.utc).isoformat()

        set_clauses = []
        params: List[Any] = []
        for column, value in payload.items():
            if isinstance(value, (dict, list)):
                set_clauses.append(f"{column} = %s::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{column} = %s")
                params.append(value)

        params.append(action_id)
        query = f"UPDATE action SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
        rows = self._get_db_handler().execute_dict_query(query, tuple(params))
        return rows[0] if rows else None
    
    def delete_action(self, action_id: str) -> bool:
        """Delete an action."""
        rows_affected = self._get_db_handler().execute_update(
            "DELETE FROM action WHERE id = %s",
            (action_id,),
        )
        return rows_affected >= 0
    
    def get_due_actions(self) -> List[Dict[str, Any]]:
        """Get all actions that are due for execution."""
        now = datetime.now(timezone.utc).isoformat()
        return self._get_db_handler().execute_dict_query(
            """
            SELECT *
            FROM action
            WHERE status = 'active'
              AND next_execution_at IS NOT NULL
              AND next_execution_at <= %s
            ORDER BY next_execution_at ASC
            """,
            (now,),
        )
    
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

        response = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO action_execution_log (
                action_id,
                status,
                executed_at,
                duration_ms,
                result_data,
                error_message
            ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            RETURNING *
            """,
            (
                log_data['action_id'],
                log_data['status'],
                log_data['executed_at'],
                log_data['duration_ms'],
                json.dumps(log_data['result_data']) if log_data['result_data'] is not None else None,
                log_data['error_message'],
            ),
        )
        
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
        
        return response[0] if response else None
    
    def get_execution_logs(self, action_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution logs for an action."""
        return self._get_db_handler().execute_dict_query(
            """
            SELECT *
            FROM action_execution_log
            WHERE action_id = %s
            ORDER BY executed_at DESC
            LIMIT %s
            """,
            (action_id, limit),
        )
    
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
