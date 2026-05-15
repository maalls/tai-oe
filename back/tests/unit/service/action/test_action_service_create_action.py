"""Tests for ActionService.create_action."""

import pytest

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self):
        self.last_payload = None

    def create_action(self, **kwargs):
        self.last_payload = kwargs
        return {"id": "a-1", **kwargs}


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_create_action_requires_mandatory_fields():
    service = ActionService(action_repo=_ActionRepoStub(), scheduler=_SchedulerStub())

    with pytest.raises(ValueError, match="Missing required field: schedule_type"):
        service.create_action(
            {"opportunity_id": "opp-1", "action_type": "recurring_quote"},
            user_id="u-1",
        )


def test_create_action_delegates_to_repository_with_defaults():
    repo = _ActionRepoStub()
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.create_action(
        {
            "opportunity_id": "opp-1",
            "action_type": "recurring_quote",
            "schedule_type": "monthly",
        },
        user_id="u-1",
    )

    assert result["id"] == "a-1"
    assert repo.last_payload["user_id"] == "u-1"
    assert repo.last_payload["schedule_config"] == {}
    assert repo.last_payload["config"] == {}
    assert repo.last_payload["max_executions"] is None
