"""Tests for ActionService.list_actions."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self):
        self.calls = []

    def list_actions(self, opportunity_id: str):
        self.calls.append(opportunity_id)
        return [{"id": "a-1", "opportunity_id": opportunity_id}]


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_list_actions_delegates_to_repository():
    repo = _ActionRepoStub()
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.list_actions("opp-1", user_id="u-1")

    assert result == [{"id": "a-1", "opportunity_id": "opp-1"}]
    assert repo.calls == ["opp-1"]
