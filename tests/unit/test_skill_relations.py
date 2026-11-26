"""Grafo de relações em JSON: uma operação atualiza o documento; a visão vem dele; a IA recebe o JSON anonimizado."""
import asyncio
import json

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.interfaces.i_skill_relation_repository import SkillRelationError
from core.use_case.skill_relations.skill_relation_use_cases import (
    GenerateRelationAdaptationsUseCase, GenerateSkillRelationsUseCase, SkillRelationUseCases, build_ai_graph, build_view,
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
        self.doc, self.revision, self.finalistic, self.plan = {"schema": 1, "related": []}, 0, finalistic, []

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

    async def plan_adaptations(self, sid, kid):
        return list(self.plan)

    async def save_finalistic_adaptation(self, sid, kid, group_id, adaptation, justification, actions):
        gid = group_id or "g1"
        self.plan = [{"id": gid, "adaptation": adaptation, "justification": justification, "actions": [{"id": "", "action": a} for a in actions]}]
        return gid

    async def candidates(self, sid, kid):
        return [s for k, s in SKILLS.items() if k != kid and (s["score"] > 0 or s["observation"])]


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
    assert '"candidates"' in ai.prompt and "EF02MA18" not in ai.prompt         # 0 estrela sem observação não é enviada
    graph = asyncio.run(build_ai_graph(repo, "s1", "k1"))
    assert graph["related"][0]["arrow"] == "none" and "id" not in graph["related"][0]  # bidirecional por padrão; sem ids internos


def test_generation_requires_a_finalistic_skill():
    res = asyncio.run(GenerateSkillRelationsUseCase(Repo(finalistic=False), Students(), Ai({}), Prompts(), Settings())
                      .execute("s1", "k1", USER))
    assert res.is_bad_request


def test_adaptation_is_only_for_the_finalistic_and_regenerating_updates_the_same_one():
    repo = Repo()
    repo.doc["related"] = [
        {"id": "r1", "kind": "skill", "skill_id": "a", "direction": "out", "origin": "ai", "reason": "", "x": None, "y": None},
        {"id": "r3", "kind": "field", "field_key": "bodyGestures", "direction": "out", "origin": "manual", "reason": "", "x": None, "y": None}]
    ai = Ai({"adaptation": "usar cartões no jogo", "justification": "apoio da comunicação", "actions": ["a1", "a2"]})
    uc = GenerateRelationAdaptationsUseCase(repo, Students(), ai, Prompts(), Settings())
    assert asyncio.run(uc.execute("s1", "k1", USER)).is_ok
    assert len(repo.plan) == 1 and repo.plan[0]["adaptation"] == "usar cartões no jogo" and len(repo.plan[0]["actions"]) == 2
    assert repo.doc["adaptation_id"] == "g1"
    assert all("adaptation" not in r for r in repo.doc["related"])           # nenhuma adaptação por relação
    assert '"fields"' in ai.prompt and "bodyGestures" in ai.prompt
    ai.raw = {"adaptation": "nova", "justification": "j", "actions": ["x"]}
    assert asyncio.run(uc.execute("s1", "k1", USER)).is_ok
    assert len(repo.plan) == 1 and repo.plan[0]["adaptation"] == "nova"      # atualizou a mesma


def test_adaptation_needs_finalistic_relations_and_a_valid_answer():
    uc = GenerateRelationAdaptationsUseCase(Repo(), Students(), Ai({}), Prompts(), Settings())
    assert asyncio.run(uc.execute("s1", "k1", USER)).is_bad_request  # sem relações
    uc = GenerateRelationAdaptationsUseCase(Repo(finalistic=False), Students(), Ai({}), Prompts(), Settings())
    assert asyncio.run(uc.execute("s1", "k1", USER)).is_bad_request
    repo = Repo()
    repo.doc["related"] = [{"id": "r1", "kind": "skill", "skill_id": "a", "direction": "out", "origin": "ai", "reason": "", "x": None, "y": None}]
    res = asyncio.run(GenerateRelationAdaptationsUseCase(repo, Students(), Ai({"adaptation": "", "actions": []}), Prompts(), Settings()).execute("s1", "k1", USER))
    assert not res.is_ok and repo.plan == []


def test_arrow_is_bidirectional_by_default_and_the_prompt_answer_can_set_it():
    repo = Repo()
    ai = Ai({"relations": [{"code": "EF05AR01", "reason": "r", "arrow": "related_to_finalistic"}, {"code": "EI03EO03", "reason": "r", "arrow": "??"}]})
    assert asyncio.run(GenerateSkillRelationsUseCase(repo, Students(), ai, Prompts(), Settings()).execute("s1", "k1", USER)).is_ok
    assert [r["direction"] for r in repo.doc["related"]] == ["in", "both"]
    manual = Repo()
    asyncio.run(_uc(manual).create("s1", "k1", {"related_skill_id": "a"}, USER))
    assert manual.doc["related"][0]["direction"] == "both"


def test_clear_removes_every_relation_and_keeps_the_finalistic_skill():
    repo = Repo()
    uc = _uc(repo)
    asyncio.run(uc.create("s1", "k1", {"related_skill_id": "a"}, USER))
    asyncio.run(uc.create("s1", "k1", {"related_skill_id": "b"}, USER))
    res = asyncio.run(uc.clear("s1", "k1", USER))
    assert res.is_ok and res.value["removed"] == 2 and repo.doc["related"] == [] and repo.finalistic


def test_preview_shows_the_anonymized_request_without_calling_the_ai():
    repo = Repo()
    repo.doc["related"] = [{"id": "r1", "kind": "skill", "skill_id": "a", "direction": "both", "origin": "ai", "reason": "Ana gosta", "x": None, "y": None}]
    for cls in (GenerateSkillRelationsUseCase, GenerateRelationAdaptationsUseCase):
        ai = Ai({})
        res = asyncio.run(cls(repo, Students(), ai, Prompts(), Settings()).preview("s1", "k1"))
        assert res.is_ok and set(res.value) == {"system", "prompt", "sources"}
        assert "Ana" not in res.value["prompt"] and ai.prompt is None and repo.revision == 0


def test_ai_gets_five_stars_and_zero_stars_only_with_observation():
    from infrastructure.services.anonymization_service import format_skill_report
    repo = Repo()
    repo.doc["related"] = [{"id": "r1", "kind": "skill", "skill_id": s, "direction": "both", "origin": "ai", "reason": "", "x": None, "y": None}
                           for s in ("z", "a", "f")]
    graph = asyncio.run(build_ai_graph(repo, "s1", "k1"))
    assert [n["code"] for n in graph["related"]] == ["EI03EO03", "EF01LP01"]          # 0 sem observação fora; 5 entra
    SKILLS["z"]["observation"] = "usa material concreto"
    assert len(asyncio.run(build_ai_graph(repo, "s1", "k1"))["related"]) == 3           # 0 com observação entra
    SKILLS["z"]["observation"] = ""
    skill = lambda code, score, obs="": {"code": code, "score": score, "description": "d", "observation": obs}
    text = format_skill_report("R", {"summary": {"by_score": {"0": 2, "5": 1}}, "groups": [
        {"grade": "1º ano", "areas": [{"area": "LP", "skills": [skill("SEMOBS", 0), skill("COMOBS", 0, "obs"), skill("CINCO", 5)]}]},
        {"grade": "2º ano", "areas": [{"area": "Mat", "skills": [skill("OUTRA", 0)]}]}]}, {})
    assert "COMOBS" in text and "CINCO" in text and "SEMOBS" not in text and "2º ano" not in text and "0=2" not in text
