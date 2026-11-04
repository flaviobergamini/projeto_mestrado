import asyncio

import core.kernel.container  # noqa: F401  (carrega o container primeiro: evita import circular)
from core.use_case.kanban.kanban_use_cases import UpdateKanbanCardUseCase


class Repo:
    def __init__(self, status):
        self.card = {"id": "c1", "student_id": "s1", "status": status, "skill_id": None}
        self.updated = None

    async def get(self, card_id):
        return self.card

    async def update(self, card_id, data):
        self.updated = data
        return {**self.card, **data}


def run(status, days):
    repo = Repo(status)
    result = asyncio.run(UpdateKanbanCardUseCase(repo).execute("c1", {"worked_days": days}))
    return result, repo


def test_days_editable_only_in_doing_and_saved_in_week_order():
    result, repo = run("doing", ["fri", "mon"])
    assert result.is_ok and repo.updated["worked_days"] == ["mon", "fri"]


def test_days_locked_in_other_columns():
    for status in ("todo", "done", "archived"):
        result, repo = run(status, ["mon"])
        assert result.is_bad_request and repo.updated is None


def test_invalid_day_rejected():
    result, _ = run("doing", ["sat"])
    assert result.is_bad_request
