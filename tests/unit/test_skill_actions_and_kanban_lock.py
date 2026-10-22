"""Ações com adaptação própria e cards do Kanban ligados a habilidade (campos do plano protegidos)."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (carrega core.kernel na ordem certa; evita import circular)
from core.services.skill_actions import (
    adaptations_as_text, dump_adaptations, flatten_actions, normalize_adaptations,
)
from core.use_case.kanban.kanban_use_cases import UpdateKanbanCardUseCase


def test_adaptation_groups_accept_new_flat_and_legacy_formats():
    new = [{"adaptation": "Fichas visuais", "justification": "Aluno responde a imagens",
            "actions": [{"action": "Usar fichas no lanche"}, "Usar fichas na roda"]}]
    g = normalize_adaptations(new)
    assert len(g) == 1 and [a["action"] for a in g[0]["actions"]] == ["Usar fichas no lanche", "Usar fichas na roda"]
    flat = [{"id": "a1", "action": "Praticar turnos", "adaptation": "Timer", "justification": "Antecipa"}]  # formato da versão anterior
    f = normalize_adaptations(flat)
    assert f[0]["adaptation"] == "Timer" and f[0]["actions"] == [{"id": "a1", "action": "Praticar turnos"}]   # id da ação preservado
    legacy = "- Primeira ação\n2) Segunda ação\n\n"                                                            # texto antigo
    assert [x["actions"][0]["action"] for x in normalize_adaptations(legacy)] == ["Primeira ação", "Segunda ação"]
    assert normalize_adaptations(None) == [] and normalize_adaptations("  ") == [] and dump_adaptations([]) is None
    assert normalize_adaptations(dump_adaptations(new))[0]["adaptation"] == "Fichas visuais"                  # ida e volta em JSON


def test_flatten_gives_one_card_per_action_with_its_adaptation():
    groups = normalize_adaptations(dump_adaptations([
        {"adaptation": "A1", "justification": "J1", "actions": ["x", "y"]},
        {"adaptation": "A2", "justification": "J2", "actions": ["z"]},
    ]))
    flat = flatten_actions(groups)
    assert [(f["action"], f["adaptation"], f["justification"]) for f in flat] == [("x", "A1", "J1"), ("y", "A1", "J1"), ("z", "A2", "J2")]
    assert len({f["id"] for f in flat}) == 3 and flat[0]["adaptation_id"] == flat[1]["adaptation_id"] != flat[2]["adaptation_id"]


def test_adaptations_as_text_for_prompts():
    txt = adaptations_as_text([{"adaptation": "A", "justification": "J", "actions": ["x"]}])
    assert txt == "- Adaptação: A | justificativa: J\n    * ação: x"


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


def test_ids_are_stable_across_edits_and_unique():
    first = normalize_adaptations(dump_adaptations([{"adaptation": "A", "actions": ["a", "b"]}]))
    ga, (x, y) = first[0]["id"], first[0]["actions"]
    assert ga and x["id"] and y["id"] and x["id"] != y["id"]
    edited = [{**first[0], "adaptation": "A editada", "actions": [{**x, "action": "a editada"}, y, {"action": "c"}]}]
    again = normalize_adaptations(dump_adaptations(edited))
    assert again[0]["id"] == ga and again[0]["actions"][0]["id"] == x["id"] and again[0]["actions"][1]["id"] == y["id"]
    assert again[0]["actions"][2]["id"] not in (x["id"], y["id"])
    dup = normalize_adaptations(dump_adaptations([{"id": "g", "actions": [{"id": "x", "action": "A"}, {"id": "x", "action": "B"}]}]))
    assert dup[0]["actions"][0]["id"] != dup[0]["actions"][1]["id"]
