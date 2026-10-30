"""Geração das adaptações por IA: fontes fixas, só habilidades elegíveis e toda adaptação com pelo menos uma ação."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.use_case.skill_plan.generate_skill_plan_draft_use_case import GenerateSkillPlanDraftUseCase
from core.use_case.skill_plan.prompts import ROUND1_SOURCES


class Students:
    async def get_by_id(self, sid):
        return {"id": sid}


class Repo:
    def __init__(self, targets):
        self.targets, self.applied = targets, None

    async def plan_skills(self, sid):
        return self.targets

    async def apply_round1(self, sid, drafts, user):
        self.applied = drafts
        return list(drafts)


class Ai:
    def __init__(self, raw):
        self.raw, self.sources, self.prompt = raw, None, None

    async def build_context(self, sid, sources):
        self.sources = sources
        return "ctx", {}

    def reanonymize(self, t, m):
        return t

    def deanonymize(self, t, m):
        return t

    async def generate_json(self, op, system, prompt, uid):
        self.prompt = prompt
        return self.raw


class Settings:
    async def get(self, key, default):
        return default


class Prompts:
    async def get(self, scope):
        return scope


T = {"skill_id": "k1", "code": "EI03EO01", "grade": "Infantil", "area": "a", "description": "d", "score": 2, "existing": "- Adaptação: antiga", "experience_fields": []}


def _run(raw, targets=(T,)):
    repo, ai = Repo(list(targets)), Ai(raw)
    res = asyncio.run(GenerateSkillPlanDraftUseCase(repo, Students(), ai, Prompts(), Settings()).execute("s1", {"user_id": "u"}))
    return res, repo, ai


def test_sources_are_fixed_and_existing_adaptations_are_sent_to_avoid_repeats():
    assert ROUND1_SOURCES == ["student", "functional_profile", "skill_report"]
    res, repo, ai = _run({"skills": []})
    assert ai.sources == ROUND1_SOURCES and "antiga" in ai.prompt and res.is_ok


def test_every_adaptation_keeps_at_least_one_action_and_unknown_codes_are_ignored():
    raw = {"skills": [
        {"code": "EI03EO01", "adaptations": [
            {"adaptation": "Fichas", "justification": "J", "actions": ["usar fichas", "revisar fichas"]},
            {"adaptation": "Sem ação", "justification": "J", "actions": []},           # descartada: precisa de pelo menos 1 ação
        ]},
        {"code": "XX00XX00", "adaptations": [{"adaptation": "x", "actions": ["y"]}]},   # código que não foi pedido
    ]}
    res, repo, _ = _run(raw)
    groups = repo.applied["k1"]["adaptations"]
    assert res.value == {"requested": 1, "filled": 1} and len(repo.applied) == 1
    assert [g["adaptation"] for g in groups] == ["Fichas"] and len(groups[0]["actions"]) == 2


def test_no_eligible_skill_is_a_bad_request():
    res, repo, ai = _run({"skills": []}, targets=())
    assert res.is_bad_request and ai.sources is None


def test_invalid_json_is_retried_once():
    class FlakyAi(Ai):
        calls = 0

        async def generate_json(self, op, system, prompt, uid):
            FlakyAi.calls += 1
            if FlakyAi.calls == 1:
                raise ValueError("Expecting ',' delimiter")
            return {"skills": [{"code": "EI03EO01", "adaptations": [{"adaptation": "A", "actions": ["x"]}]}]}

    repo, ai = Repo([T]), FlakyAi({})
    res = asyncio.run(GenerateSkillPlanDraftUseCase(repo, Students(), ai, Prompts(), Settings()).execute("s1", {}))
    assert res.is_ok and FlakyAi.calls == 2 and repo.applied
