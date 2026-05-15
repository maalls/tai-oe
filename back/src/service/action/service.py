"""Application service for action-related use-cases."""

from typing import Any, Dict, List, Optional

from src.repository.action_repository import ActionRepository
from src.service.action_scheduler import ActionScheduler


class ActionService:
    """Service orchestrating action CRUD and execution workflows."""

    def __init__(
        self,
        action_repo: Optional[ActionRepository] = None,
        scheduler: Optional[ActionScheduler] = None,
    ):
        self.action_repo = action_repo or ActionRepository()
        self.scheduler = scheduler or ActionScheduler()

    def list_actions(self, opportunity_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        _ = user_id
        return self.action_repo.list_actions(opportunity_id)

    def create_action(self, data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        required_fields = ["opportunity_id", "action_type", "schedule_type"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return self.action_repo.create_action(
            user_id=user_id,
            opportunity_id=data["opportunity_id"],
            action_type=data["action_type"],
            schedule_type=data["schedule_type"],
            schedule_config=data.get("schedule_config", {}),
            config=data.get("config", {}),
            max_executions=data.get("max_executions"),
        )

    def get_action(self, action_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        _ = user_id
        return self.action_repo.get_action(action_id)

    def update_action(self, action_id: str, data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        _ = user_id
        action = self.action_repo.get_action(action_id)
        if not action:
            return None
        return self.action_repo.update_action(action_id, data)

    def delete_action(self, action_id: str, user_id: str) -> bool:
        _ = user_id
        action = self.action_repo.get_action(action_id)
        if not action:
            return False
        self.action_repo.delete_action(action_id)
        return True

    def pause_action(self, action_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        _ = user_id
        return self.action_repo.pause_action(action_id)

    def resume_action(self, action_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        _ = user_id
        return self.action_repo.resume_action(action_id)

    def execute_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        _ = user_id
        return self.scheduler.execute_manually(action_id)

    def get_action_logs(self, action_id: str, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        _ = user_id
        return self.action_repo.get_execution_logs(action_id, limit=limit)
