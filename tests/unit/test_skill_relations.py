"""Grafo de relações em JSON: uma operação atualiza o documento; a visão vem dele; a IA recebe o JSON anonimizado."""
import asyncio
import json

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.interfaces.i_skill_relation_repository import SkillRelationError
from core.use_case.skill_relations.skill_relation_use_cases import (
    GenerateSkillRelationsUseCase, SkillRelationUseCases, build_ai_graph, build_view,
)

SKILLS = {
    "k1": {"id": "k1", "code": "EI03EO02", "grade": "Infantil", "area": "O eu", "description": "mãe", "score": 4, "observation": "Ana usa cartões"},
    "a": {"id": "a", "code": "EI03EO03", "grade": "Infantil", "area": "O eu", "description": "A", "score": 3, "observation": ""},
    "b": {"id": "b", "code": "EF05AR01", "grade": "5º ano", "area": "Arte", "description": "B", "score": 1, "observation": "o"},
    "z": {"id": "z", "code": "EF02MA18", "grade": "2º ano", "area": "Mat", "description": "Z", "score": 0, "observation": ""},
    "f": {"id": "f", "code": "EF01LP01", "grade": "1º ano", "area": "LP", "description": "F", "score": 5, "observation": ""},
}


class Students:
    async def get_by_id(self, sid):
        return {"id": sid}


class Repo:
    def __init__(self, finalistic=True):
        self.doc, self.revision, self.finalistic = {"schema": 1, "related": []}, 0, finalistic

    async def get_document(self, sid, kid):
        return json.loads(json.dumps(self.doc)), self.revision

    async def mutate(self, sid, kid, change, user):
        doc = json.loads(json.dumps(self.doc))
        change(doc)  # aborta sem gravar se levantar
        self.doc, self.revision = doc, self.revision + 1
        return doc, self.revision

    async def find_skill_of_relation(self, sid, rid):
        return "k1" if any(r["id"] == rid for r in self.doc["related"]) else None

    async def skill_info(self, sid, kid):
        return {**SKILLS[kid], "finalistic": self.finalistic} if kid in SKILLS else None

    async def skill_briefs(self, sid, ids):
        return {i: SKILLS[i] for i in ids if i in SKILLS}

    async def candidates(self, sid, kid):
        return [s for k, s in SKILLS.items() if k != kid and 1 <= s["score"] <= 4]


class Ai:
    def __init__(self, raw=None):
        self.raw, self.prompt = raw, None

    async def build_context(self, sid, sources, **kwargs):
        return "ctx", {"Ana Silva": "ALUNO_1"}

    def reanonymize(self, t, m):
        for real, alias in m.items():
            t = t.replace(real.split()[0], alias)
        return t

    def deanonymize(self, t, m):
        return t

    async def generate_json(self, op, system, prompt, uid, with_bncc_catalog=False):
        self.prompt = prompt
        return self.raw


class Settings:
    async def get(self, key, default):
        return default


class Prompts:
    async def get(self, scope):
        return scope


USER = {"user_id": "u", "username": "prof"}


def _uc(repo):
    return SkillRelationUseCases(repo)


def test_create_updates_json_and_view_is_built_from_it():
    repo = Repo()
    res = asyncio.run(_uc(repo).create("s1", "k1", {"related_skill_id": "a", "direction": "in", "reason": "apoio"}, USER))
    assert res.is_ok and repo.revision == 1
    assert repo.doc["related"][0]["skill_id"] == "a" and repo.doc["related"][0]["direction"] == "in"
    view = asyncio.run(build_view(repo, "s1", "k1"))
    assert view["revision"] == 1 and view["relations"][0]["related_skill"]["score"] == 3  # estrelas vêm da nota, não do JSON
    SKILLS["a"]["score"] = 4                                                               # o professor mudou a nota...
    assert asyncio.run(build_view(repo, "s1", "k1"))["relations"][0]["related_skill"]["score"] == 4  # ...o mapa reflete na hora
    SKILLS["a"]["score"] = 3


def test_rules_finalistic_only_and_one_to_four_stars():
    uc = _uc(Repo(finalistic=False))
    assert asyncio.run(uc.create("s1", "k1", {"related_skill_id": "a"}, USER)).is_bad_request
    uc = _uc(Repo())
    for bad in ("z", "f", "k1"):  # 0 estrela, 5 estrelas, ela mesma
        assert asyncio.run(uc.create("s1", "k1", {"related_skill_id": bad}, USER)).is_bad_request
    assert asyncio.run(uc.create("s1", "k1", {"related_skill_id": "a"}, USER)).is_ok
    assert asyncio.run(uc.create("s1", "k1", {"related_skill_id": "a"}, USER)).is_bad_request  # repetida


def test_update_layout_and_delete_change_the_same_document():
    repo = Repo()
    uc = _uc(repo)
    rid = asyncio.run(uc.create("s1", "k1", {"related_skill_id": "a"}, USER)).value["id"]
    asyncio.run(uc.update("s1", rid, {"direction": "in", "justification": "novo motivo"}, USER))
    asyncio.run(uc.set_layout("s1", "k1", {rid: {"x": 10.0, "y": 20.0}}, USER))
    r = repo.doc["related"][0]
    assert (r["direction"], r["reason"], r["x"], r["y"]) == ("in", "novo motivo", 10.0, 20.0) and repo.revision == 3
    asyncio.run(uc.delete("s1", rid, USER))
    assert repo.doc["related"] == [] and repo.revision == 4


def test_persisted_nodes_always_show_including_fields_and_zero_stars():
    repo = Repo()
    repo.doc["related"] = [{"id": "r1", "kind": "skill", "skill_id": "z", "direction": "out", "origin": "ai", "reason": "", "x": None, "y": None},
                           {"id": "r2", "kind": "field", "field_key": "bodyGestures", "direction": "out", "origin": "manual",
                            "reason": "r", "adaptation": "ad", "actions": ["a"], "x": None, "y": None}]
    view = asyncio.run(build_view(repo, "s1", "k1"))
    assert [(r["id"], r["kind"]) for r in view["relations"]] == [("r1", "skill"), ("r2", "field")]
    assert view["relations"][0]["related_skill"]["score"] == 0 and view["relations"][1]["field_key"] == "bodyGestures"


def test_ai_receives_anonymized_graph_json_and_only_valid_picks_are_saved():
    repo = Repo()
    ai = Ai({"relations": [{"code": "EF05AR01", "reason": "apoia"}, {"code": "EF05AR01", "reason": "repetida"},
                           {"code": "EF02MA18", "reason": "0 estrela"}, {"code": "XX00", "reason": "inventada"}]})
    res = asyncio.run(GenerateSkillRelationsUseCase(repo, Students(), ai, Prompts(), Settings()).execute("s1", "k1", USER))
    assert res.is_ok and res.value["created"] == 1
    assert [r["skill_id"] for r in repo.doc["related"]] == ["b"] and repo.doc["related"][0]["origin"] == "ai"
    assert "Ana" not in ai.prompt and "ALUNO_1 usa cartões" in ai.prompt        # nome real some, até dentro das observações
    assert '"candidates"' in ai.prompt and "EF02MA18" not in ai.prompt         # só candidatas com 1 a 4 estrelas
    graph = asyncio.run(build_ai_graph(repo, "s1", "k1"))
    assert graph["related"][0]["arrow"] == "finalistic_to_related" and "id" not in graph["related"][0]  # sem ids internos


def test_generation_requires_a_finalistic_skill():
    res = asyncio.run(GenerateSkillRelationsUseCase(Repo(finalistic=False), Students(), Ai({}), Prompts(), Settings())
                      .execute("s1", "k1", USER))
    assert res.is_bad_request
