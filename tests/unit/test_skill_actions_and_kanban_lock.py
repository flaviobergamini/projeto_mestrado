"""Ações com adaptação própria e cards do Kanban ligados a habilidade (campos do plano protegidos)."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (carrega core.kernel na ordem certa; evita import circular)
from core.services.skill_actions import actions_as_text, dump_actions, normalize_actions
from core.use_case.kanban.kanban_use_cases import UpdateKanbanCardUseCase


def test_actions_accept_list_json_and_legacy_text():
    items = [{"action": "Usar fichas visuais", "adaptation": "Fichas com fotos reais"}, "Praticar turnos"]
    n = normalize_actions(items)
    assert n == [{"action": "Usar fichas visuais", "adaptation": "Fichas com fotos reais"},
                 {"action": "Praticar turnos", "adaptation": ""}]
    assert normalize_actions(dump_actions(items)) == n                      # ida e volta em JSON
    legacy = "- Primeira ação\n2) Segunda ação\n\n"                       # texto antigo, uma ação por linha
    assert [a["action"] for a in normalize_actions(legacy)] == ["Primeira ação", "Segunda ação"]
    assert normalize_actions(None) == [] and normalize_actions("   ") == [] and dump_actions([]) is None


def test_actions_as_text_for_prompts():
    txt = actions_as_text([{"action": "A", "adaptation": "x"}, {"action": "B", "adaptation": ""}])
    assert txt == "- A (adaptação: x)\n- B"


class FakeKanbanRepo:
    def __init__(self, card):
        self.card, self.updated = card, None

    async def get(self, card_id):
        return self.card

    async def update(self, card_id, data):
        self.updated = data
        return {**self.card, **data}


SKILL_CARD = {"id": "c1", "skill_id": "k1", "title": "Usar fichas", "description": None, "adaptation": "Fichas reais", "daily_log": ""}
MANUAL_CARD = {"id": "c2", "skill_id": None, "title": "Livre", "description": "d", "adaptation": None, "daily_log": ""}


def _update(card, data):
    repo = FakeKanbanRepo(card)
    return asyncio.run(UpdateKanbanCardUseCase(repo).execute(card["id"], data)), repo


def test_skill_card_title_description_and_adaptation_are_locked():
    for field, value in (("title", "Outro"), ("description", "texto"), ("adaptation", "Mudou")):
        result, repo = _update(SKILL_CARD, {field: value})
        assert result.is_bad_request and repo.updated is None, field


def test_skill_card_allows_diary_column_and_reaction_and_same_values():
    result, repo = _update(SKILL_CARD, {"daily_log": "Hoje fez sozinho", "status": "doing", "reaction": 4,
                                        "title": "Usar fichas", "adaptation": "Fichas reais"})
    assert result.is_ok
    assert repo.updated == {"daily_log": "Hoje fez sozinho", "status": "doing", "reaction": 4}  # campos travados nunca são gravados


def test_manual_card_stays_fully_editable():
    result, repo = _update(MANUAL_CARD, {"title": "Novo", "description": "x"})
    assert result.is_ok and repo.updated == {"title": "Novo", "description": "x"}
