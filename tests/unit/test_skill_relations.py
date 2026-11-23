"""Relações entre habilidades: a IA só cria relações válidas (código existente, campo conhecido, com ação)."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.interfaces.i_skill_relation_repository import SkillRelationError
from core.use_case.skill_relations.skill_relation_use_cases import GenerateSkillRelationsUseCase


class Students:
    async def get_by_id(self, sid):
        return {"id": sid}


class Repo:
    def __init__(self):
        self.created, self.existing = [], []

    async def skill_info(self, sid, kid):
        return {"id": kid, "code": "EF05LP01", "grade": "5º ano", "area": "Língua Portuguesa", "description": "d",
                "score": 2, "finalistic": True}

    async def list_relations(self, sid, kid):
        return self.existing

    async def candidate_codes(self, sid, kid):
        return {"EF05AR01": "d"}

    async def resolve_codes(self, codes):
        return {c: {"id": f"id-{c}", "code": c} for c in codes if c == "EF05AR01"}  # só este código existe no catálogo

    async def create(self, sid, kid, data, user, source):
        if data.get("related_skill_id") == "id-EF05AR01" and any(c["related_skill_id"] == "id-EF05AR01" for c in self.created):
            raise SkillRelationError("Essa relação já existe.")
        self.created.append({**data, "source": source})
        return {"id": f"r{len(self.created)}", **data}


class Ai:
    def __init__(self, raw):
        self.raw, self.prompt, self.catalog = raw, None, None

    async def build_context(self, sid, sources, **kwargs):
        return "ctx", {}

    def reanonymize(self, t, m):
        return t

    def deanonymize(self, t, m):
        return t

    async def generate_json(self, op, system, prompt, uid, with_bncc_catalog=False):
        self.prompt, self.catalog = prompt, with_bncc_catalog
        return self.raw


class Settings:
    async def get(self, key, default):
        return default


class Prompts:
    async def get(self, scope):
        return scope


def _run(raw):
    repo, ai = Repo(), Ai(raw)
    res = asyncio.run(GenerateSkillRelationsUseCase(repo, Students(), ai, Prompts(), Settings()).execute("s1", "k1", {"user_id": "u"}))
    return res, repo, ai


def test_only_valid_relations_are_created_and_catalog_is_sent():
    raw = {"relations": [
        {"kind": "skill", "code": "EF05AR01", "adaptation": "A", "justification": "J", "actions": ["a1", "a2"]},
        {"kind": "skill", "code": "XX00XX00", "adaptation": "A", "actions": ["a"]},        # código inventado: descartado
        {"kind": "field", "field": "selfOtherUs", "adaptation": "B", "justification": "J", "actions": ["b"]},
        {"kind": "field", "field": "campoInexistente", "adaptation": "B", "actions": ["b"]},  # campo inválido: descartado
        {"kind": "field", "field": "bodyGestures", "adaptation": "C", "actions": []},       # sem ação: descartado
        {"kind": "skill", "code": "EF05AR01", "adaptation": "A2", "actions": ["x"]},        # repetida: descartada
    ]}
    res, repo, ai = _run(raw)
    assert res.is_ok and res.value["created"] == 2 and res.value["skipped"] == 4
    assert [c["kind"] for c in repo.created] == ["skill", "field"] and all(c["source"] == "ai" for c in repo.created)
    assert ai.catalog is True                                   # catálogo BNCC anexado para a IA citar códigos reais
    assert "FINALÍSTICA" in ai.prompt            # a finalística é avisada à IA


def test_actions_respect_the_configured_maximum():
    raw = {"relations": [{"kind": "field", "field": "spacesTimes", "adaptation": "A", "justification": "J",
                          "actions": [f"a{i}" for i in range(9)]}]}
    res, repo, _ = _run(raw)
    assert res.is_ok and len(repo.created[0]["actions"]) == 5   # padrão: máx. 5 ações por relação
