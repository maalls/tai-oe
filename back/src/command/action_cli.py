#!/usr/bin/env python3
"""
CLI tool for managing actions.

Usage:
    python src/command/action_cli.py list-actions <opportunity_id>
    python src/command/action_cli.py create-action <opportunity_id> <user_id> <action_type> <schedule_type>
    python src/command/action_cli.py get-action <action_id>
    python src/command/action_cli.py delete-action <action_id>
    python src/command/action_cli.py pause-action <action_id>
    python src/command/action_cli.py resume-action <action_id>
    python src/command/action_cli.py execute-action <action_id>
    python src/command/action_cli.py get-logs <action_id>
"""

import sys
import json
from typing import Optional
from src.repository.action_repository import ActionRepository
from src.service.action_scheduler import ActionScheduler
from dotenv import load_dotenv

load_dotenv()


class ActionCLI:
    """Command-line interface for action management."""
    
    def __init__(self):
        self.repo = ActionRepository()
        self.scheduler = ActionScheduler()
    
    def list_actions(self, opportunity_id: str):
        """List all actions for an opportunity."""
        actions = self.repo.list_actions(opportunity_id)
        
        if not actions:
            print(f"No actions found for opportunity {opportunity_id}")
            return
        
        print(f"\n{'='*100}")
        print(f"Actions for opportunity: {opportunity_id}")
        print(f"{'='*100}\n")
        
        for i, action in enumerate(actions, 1):
            print(f"{i}. Action ID: {action['id']}")
            print(f"   Type: {action['action_type']}")
            print(f"   Status: {action['status']}")
            print(f"   Schedule: {action['schedule_type']}")
            print(f"   Next execution: {action.get('next_execution_at', 'N/A')}")
            print(f"   Executions: {action.get('execution_count', 0)}/{action.get('max_executions', 'unlimited')}")
            print(f"   Created: {action.get('created_at', 'N/A')}")
            print(f"   Config: {json.dumps(action.get('config', {}), indent=6)}")
            print()
    
    def create_action(self, opportunity_id: str, user_id: str, action_type: str,
                     schedule_type: str, schedule_config_json: str = None,
                     config_json: str = None, max_executions: int = None):
        """Create a new action."""
        
        # Parse JSON configs
        schedule_config = {}
        if schedule_config_json:
            try:
                schedule_config = json.loads(schedule_config_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing schedule_config JSON: {e}")
                return
        
        # Default schedule config based on type
        if not schedule_config:
            if schedule_type == 'monthly':
                schedule_config = {'day_of_month': 1, 'time': '09:00', 'timezone': 'UTC'}
            elif schedule_type == 'weekly':
                schedule_config = {'day_of_week': 1, 'time': '09:00', 'timezone': 'UTC'}
            elif schedule_type == 'daily':
                schedule_config = {'time': '09:00', 'timezone': 'UTC'}
            else:
                schedule_config = {}
        
        config = {}
        if config_json:
            try:
                config = json.loads(config_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing config JSON: {e}")
                return
        
        # Create action
        action = self.repo.create_action(
            user_id=user_id,
            opportunity_id=opportunity_id,
            action_type=action_type,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            config=config,
            max_executions=max_executions
        )
        
        if action:
            print(f"\n✓ Action created successfully!")
            print(f"Action ID: {action['id']}")
            print(f"Next execution: {action.get('next_execution_at')}")
        else:
            print(f"✗ Failed to create action")
    
    def get_action(self, action_id: str):
        """Get action details."""
        action = self.repo.get_action(action_id)
        
        if not action:
            print(f"Action {action_id} not found")
            return
        
        print(f"\n{'='*100}")
        print(f"Action Details: {action_id}")
        print(f"{'='*100}\n")
        print(f"Type: {action['action_type']}")
        print(f"Status: {action['status']}")
        print(f"Opportunity: {action['opportunity_id']}")
        print(f"User: {action['user_id']}")
        print(f"Schedule Type: {action['schedule_type']}")
        print(f"Schedule Config: {json.dumps(action.get('schedule_config', {}), indent=2)}")
        print(f"Config: {json.dumps(action.get('config', {}), indent=2)}")
        print(f"Last executed: {action.get('last_executed_at', 'Never')}")
        print(f"Next execution: {action.get('next_execution_at', 'N/A')}")
        print(f"Execution count: {action.get('execution_count', 0)}")
        print(f"Max executions: {action.get('max_executions', 'Unlimited')}")
        print(f"Created: {action.get('created_at')}")
        print(f"Updated: {action.get('updated_at')}")
        print()
    
    def delete_action(self, action_id: str):
        """Delete an action."""
        self.repo.delete_action(action_id)
        print(f"✓ Action {action_id} deleted")
    
    def pause_action(self, action_id: str):
        """Pause an action."""
        self.repo.pause_action(action_id)
        print(f"✓ Action {action_id} paused")
    
    def resume_action(self, action_id: str):
        """Resume a paused action."""
        self.repo.resume_action(action_id)
        print(f"✓ Action {action_id} resumed")
    
    def execute_action(self, action_id: str):
        """Manually execute an action."""
        result = self.scheduler.execute_manually(action_id)
        
        print(f"\n{'='*100}")
        print(f"Action Execution Result")
        print(f"{'='*100}\n")
        print(f"Action ID: {result['action_id']}")
        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration_ms']}ms")
        if result['result']:
            print(f"Result: {json.dumps(result['result'], indent=2)}")
        if result['error']:
            print(f"Error: {result['error']}")
        print()
    
    def get_logs(self, action_id: str, limit: int = 10):
        """Get execution logs for an action."""
        logs = self.repo.get_execution_logs(action_id, limit=limit)
        
        if not logs:
            print(f"No execution logs found for action {action_id}")
            return
        
        print(f"\n{'='*100}")
        print(f"Execution Logs: {action_id} (showing last {limit})")
        print(f"{'='*100}\n")
        
        for i, log in enumerate(logs, 1):
            print(f"{i}. Executed: {log['executed_at']}")
            print(f"   Status: {log['status']}")
            print(f"   Duration: {log.get('duration_ms', 'N/A')}ms")
            if log.get('result_data'):
                print(f"   Result: {json.dumps(log['result_data'], indent=6)}")
            if log.get('error_message'):
                print(f"   Error: {log['error_message']}")
            print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    cli = ActionCLI()
    
    try:
        if command == 'list-actions':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py list-actions <opportunity_id>")
                return
            cli.list_actions(sys.argv[2])
        
        elif command == 'create-action':
            if len(sys.argv) < 5:
                print("Usage: action_cli.py create-action <opportunity_id> <user_id> <action_type> <schedule_type> [schedule_config_json] [config_json] [max_executions]")
                return
            cli.create_action(
                sys.argv[2],  # opportunity_id
                sys.argv[3],  # user_id
                sys.argv[4],  # action_type
                sys.argv[5],  # schedule_type
                sys.argv[6] if len(sys.argv) > 6 else None,  # schedule_config_json
                sys.argv[7] if len(sys.argv) > 7 else None,  # config_json
                int(sys.argv[8]) if len(sys.argv) > 8 else None,  # max_executions
            )
        
        elif command == 'get-action':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py get-action <action_id>")
                return
            cli.get_action(sys.argv[2])
        
        elif command == 'delete-action':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py delete-action <action_id>")
                return
            cli.delete_action(sys.argv[2])
        
        elif command == 'pause-action':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py pause-action <action_id>")
                return
            cli.pause_action(sys.argv[2])
        
        elif command == 'resume-action':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py resume-action <action_id>")
                return
            cli.resume_action(sys.argv[2])
        
        elif command == 'execute-action':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py execute-action <action_id>")
                return
            cli.execute_action(sys.argv[2])
        
        elif command == 'get-logs':
            if len(sys.argv) < 3:
                print("Usage: action_cli.py get-logs <action_id> [limit]")
                return
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            cli.get_logs(sys.argv[2], limit=limit)
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
