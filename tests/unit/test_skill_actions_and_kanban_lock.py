"""Ações com adaptação própria e cards do Kanban ligados a habilidade (campos do plano protegidos)."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (carrega core.kernel na ordem certa; evita import circular)
from core.services.skill_actions import actions_as_text, dump_actions, normalize_actions
from core.use_case.kanban.kanban_use_cases import UpdateKanbanCardUseCase


def test_actions_accept_list_json_and_legacy_text():
    items = [{"action": "Usar fichas visuais", "adaptation": "Fichas com fotos reais"}, "Praticar turnos"]
    n = normalize_actions(items)
    assert n == [{"id": "", "action": "Usar fichas visuais", "adaptation": "Fichas com fotos reais", "justification": ""},
                 {"id": "", "action": "Praticar turnos", "adaptation": "", "justification": ""}]
    stored = normalize_actions(dump_actions(items))                        # ida e volta em JSON
    assert [{k: v for k, v in a.items() if k != 'id'} for a in stored] == [{k: v for k, v in a.items() if k != 'id'} for a in n]
    legacy = "- Primeira ação\n2) Segunda ação\n\n"                       # texto antigo, uma ação por linha
    assert [a["action"] for a in normalize_actions(legacy)] == ["Primeira ação", "Segunda ação"]
    assert normalize_actions(None) == [] and normalize_actions("   ") == [] and dump_actions([]) is None


def test_actions_as_text_for_prompts():
    txt = actions_as_text([{"action": "A", "adaptation": "x"}, {"action": "B", "adaptation": ""}])
    assert txt == "- A (adaptação: x)\n- B"


class FakeKanbanRepo:
    def __init__(self, card):
        self.card, self.updated, self.synced = card, None, []

    async def sync_skill_score(self, student_id, skill_id):
        self.synced.append((student_id, skill_id))

    async def delete(self, card_id):
        return True

    async def get(self, card_id):
        return self.card

    async def update(self, card_id, data):
        self.updated = data
        return {**self.card, **data}


SKILL_CARD = {"id": "c1", "student_id": "s1", "status": "todo", "skill_id": "k1", "title": "Usar fichas", "description": None, "adaptation": "Fichas reais", "daily_log": ""}
MANUAL_CARD = {"id": "c2", "student_id": "s1", "skill_id": None, "title": "Livre", "description": "d", "adaptation": None, "daily_log": ""}


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


def test_reaction_5_moves_card_to_done_and_recalculates_skill_score():
    result, repo = _update(SKILL_CARD, {"reaction": 5})
    assert result.is_ok and repo.updated == {"reaction": 5, "status": "done"}
    assert repo.synced == [("s1", "k1")]


def test_manual_card_does_not_touch_skill_score():
    result, repo = _update(MANUAL_CARD, {"status": "done"})
    assert result.is_ok and repo.synced == []


def test_summary_requires_diary_and_respects_no_ai():
    from core.use_case.kanban.kanban_use_cases import GenerateKanbanCardSummaryUseCase

    class Ai:
        def __init__(self): self.calls = 0
        async def build_context(self, sid, src): return "", {}
        def reanonymize(self, t, m): return t
        def deanonymize(self, t, m): return t
        async def generate_text(self, *a): self.calls += 1; return "Resumo."

    class Prompts:
        async def get(self, scope): return scope

    class Skills:
        def __init__(self, excluded): self.excluded = excluded
        async def skill_context(self, s, k): return {"ai_excluded": self.excluded}

    def run(card, excluded=False):
        repo, ai = FakeKanbanRepo(card), Ai()
        uc = GenerateKanbanCardSummaryUseCase(repo, Skills(excluded), None, ai, Prompts())
        return asyncio.run(uc.execute("c1", {"user_id": "u"})), repo, ai

    assert run(SKILL_CARD)[0].is_bad_request                                   # sem diário
    ok, repo, ai = run({**SKILL_CARD, "daily_log": "fez sozinho"})
    assert ok.is_ok and repo.updated == {"summary": "Resumo."} and ai.calls == 1
    blocked, _, ai = run({**SKILL_CARD, "daily_log": "x"}, excluded=True)
    assert blocked.is_bad_request and ai.calls == 0


def test_set_id_is_stable_across_edits_and_unique():
    first = normalize_actions(dump_actions([{"action": "A"}, {"action": "B"}]))
    assert all(a["id"] for a in first) and first[0]["id"] != first[1]["id"]
    edited = [{**first[0], "action": "A editada", "adaptation": "nova"}, first[1], {"action": "C"}]  # só o id mantém o vínculo com o card
    again = normalize_actions(dump_actions(edited))
    assert again[0]["id"] == first[0]["id"] and again[1]["id"] == first[1]["id"] and again[2]["id"] not in {a["id"] for a in first}
    dup = normalize_actions(dump_actions([{"id": "x", "action": "A"}, {"id": "x", "action": "B"}]))
    assert dup[0]["id"] != dup[1]["id"]
