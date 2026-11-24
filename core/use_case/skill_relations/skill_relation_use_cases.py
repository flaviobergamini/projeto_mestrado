"""Relações entre habilidades. O grafo é UM documento JSON por aluno + habilidade finalística (fonte única): a tela é
desenhada a partir dele e a IA recebe uma versão anonimizada dele. Regra aqui; HTTP nas rotas."""
import json
import logging
import uuid
from datetime import date, timedelta
from typing import Optional

from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_relation_repository import ISkillRelationRepository, SkillRelationError
from core.interfaces.i_student_reader import IStudentReader
from core.kernel.result import Result
from core.use_case.skill_plan.prompts import SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_SETTINGS, resolve_round1_settings

logger = logging.getLogger(__name__)

MAX_RELATIONS = 6  # teto de relações novas por geração (a IA usa menos quando o caso pede)
FIELD_NAMES = {
    "selfOtherUs": "O eu, o outro e o nós", "bodyGestures": "Corpo, gestos e movimentos",
    "linesSounds": "Traços, sons, cores e formas", "listeningSpeaking": "Escuta, fala, pensamento e imaginação",
    "spacesTimes": "Espaços, tempos, quantidades, relações e transformações",
}
MIN_STARS, MAX_STARS = 1, 4  # só habilidades em andamento entram no grafo (0 = não avaliada, 5 = concluída)


def _in_range(score: int) -> bool:
    return MIN_STARS <= (score or 0) <= MAX_STARS


def _public(brief: dict) -> dict:
    return {k: brief[k] for k in ("id", "code", "grade", "area", "description", "score")}


async def build_view(repo: ISkillRelationRepository, student_id: str, skill_id: str) -> Optional[dict]:
    """O que a tela desenha: o documento JSON + dados vivos (código, descrição e ESTRELAS ATUAIS de cada nó)."""
    info = await repo.skill_info(student_id, skill_id)
    if not info:
        return None
    doc, revision = await repo.get_document(student_id, skill_id)
    briefs = await repo.skill_briefs(student_id, [r["skill_id"] for r in doc["related"] if r.get("skill_id")])
    relations = []
    for r in doc["related"]:  # tudo o que está no JSON aparece (a regra de 1 a 4 estrelas vale para CRIAR, não para esconder)
        is_field = r.get("kind") == "field"
        if not is_field and r.get("skill_id") not in briefs:
            continue
        relations.append({
            "id": r["id"], "skill_id": skill_id, "kind": "field" if is_field else "skill",
            "field_key": r.get("field_key") if is_field else None,
            "related_skill": None if is_field else _public(briefs[r["skill_id"]]),
            "direction": r.get("direction") or "out", "justification": r.get("reason") or "",
            "adaptation": r.get("adaptation") or "", "actions": r.get("actions") or [],
            "source": r.get("origin") or "manual", "created_by": None, "x": r.get("x"), "y": r.get("y"),
        })
    return {"skill": {k: v for k, v in info.items() if k != "observation"}, "relations": relations,
            "revision": revision, "document": doc}


async def build_ai_graph(repo: ISkillRelationRepository, student_id: str, skill_id: str, with_candidates: bool = False) -> Optional[dict]:
    """O grafo em JSON para a IA: SEM ids e sem nome de aluno; só códigos, descrições, estrelas, observações, direção e motivo."""
    info = await repo.skill_info(student_id, skill_id)
    if not info:
        return None
    doc, _ = await repo.get_document(student_id, skill_id)
    briefs = await repo.skill_briefs(student_id, [r["skill_id"] for r in doc["related"] if r.get("skill_id")])

    def node(b: dict) -> dict:
        return {"code": b["code"], "grade": b["grade"], "area": b["area"], "description": b["description"],
                "stars": b["score"], "observation": b.get("observation") or ""}

    out = {
        "finalistic": node(info),
        "related": [
            {**node(briefs[r["skill_id"]]),
             "arrow": "finalistic_to_related" if (r.get("direction") or "out") == "out" else "related_to_finalistic",
             "origin": r.get("origin") or "manual", "reason": r.get("reason") or ""}
            for r in doc["related"] if r.get("skill_id") in briefs
        ],
    }
    if with_candidates:
        linked = {r.get("skill_id") for r in doc["related"]}
        out["candidates"] = [node(c) for c in await repo.candidates(student_id, skill_id) if c["id"] not in linked]
    return out


def _find(doc: dict, relation_id: str) -> Optional[dict]:
    return next((r for r in doc["related"] if r.get("id") == relation_id), None)


class SkillRelationUseCases:
    """Leitura e edição do grafo (cada operação atualiza o JSON de forma atômica e sobe a revisão)."""

    def __init__(self, repository: ISkillRelationRepository) -> None:
        self.repository = repository

    async def overview(self, student_id: str) -> Result:
        return Result.ok(await self.repository.overview(student_id))

    async def list_relations(self, student_id: str, skill_id: str) -> Result:
        view = await build_view(self.repository, student_id, skill_id)
        return Result.ok(view) if view else Result.not_found("Habilidade não encontrada.")

    async def graph_json(self, student_id: str, skill_id: str) -> Result:
        graph = await build_ai_graph(self.repository, student_id, skill_id)
        return Result.ok(graph) if graph else Result.not_found("Habilidade não encontrada.")

    async def create(self, student_id: str, skill_id: str, data: dict, user: dict) -> Result:
        mother = await self.repository.skill_info(student_id, skill_id)
        if not mother:
            return Result.not_found("Habilidade não encontrada.")
        if not mother["finalistic"]:
            return Result.bad_request("Marque a habilidade como finalística antes de relacioná-la com outras.")
        related_id = data.get("related_skill_id")
        if not related_id or related_id == skill_id:
            return Result.bad_request("Escolha outra habilidade para relacionar.")
        related = (await self.repository.skill_briefs(student_id, [related_id])).get(related_id)
        if not related:
            return Result.bad_request("Habilidade relacionada não encontrada.")
        if not _in_range(related["score"]):
            return Result.bad_request("Só habilidades com 1 a 4 estrelas podem ser relacionadas.")
        new = {"id": str(uuid.uuid4()), "kind": "skill", "skill_id": related_id, "direction": "in" if data.get("direction") == "in" else "out",
               "origin": "manual", "reason": (data.get("reason") or "").strip(), "x": data.get("x"), "y": data.get("y")}

        def change(doc: dict) -> None:
            if any(r.get("skill_id") == related_id for r in doc["related"]):
                raise SkillRelationError("Essa relação já existe.")
            doc["related"].append(new)

        try:
            await self.repository.mutate(student_id, skill_id, change, user)
        except SkillRelationError as e:
            return Result.bad_request(str(e))
        return Result.ok({"id": new["id"]})

    async def update(self, student_id: str, relation_id: str, data: dict, user: dict) -> Result:
        skill_id = await self.repository.find_skill_of_relation(student_id, relation_id)
        if not skill_id:
            return Result.not_found("Relação não encontrada.")

        def change(doc: dict) -> None:
            r = _find(doc, relation_id)
            if not r:
                raise SkillRelationError("Relação não encontrada.")
            if data.get("direction") in ("in", "out"):
                r["direction"] = data["direction"]
            if data.get("adaptation") is not None:
                r["adaptation"], r["adaptation_origin"] = str(data["adaptation"]).strip(), "manual"
            if isinstance(data.get("actions"), list):
                r["actions"] = [str(a).strip() for a in data["actions"] if str(a).strip()]
                r["adaptation_origin"] = "manual"
            reason = data.get("reason", data.get("justification"))
            if reason is not None:
                r["reason"] = str(reason).strip()
                r["origin"] = "manual"  # editada por uma pessoa
            if "x" in data and "y" in data:
                r["x"], r["y"] = data["x"], data["y"]

        try:
            await self.repository.mutate(student_id, skill_id, change, user)
        except SkillRelationError as e:
            return Result.not_found(str(e))
        return Result.ok({"id": relation_id})

    async def set_layout(self, student_id: str, skill_id: str, positions: dict, user: dict) -> Result:
        """Posições dos nós no mapa ({id: {x, y}}; valor nulo limpa a posição de volta ao layout padrão)."""
        def change(doc: dict) -> None:
            for r in doc["related"]:
                if r["id"] in positions:
                    p = positions[r["id"]]
                    r["x"], r["y"] = (p["x"], p["y"]) if p else (None, None)

        await self.repository.mutate(student_id, skill_id, change, user)
        return Result.ok({"saved": len(positions)})

    async def delete(self, student_id: str, relation_id: str, user: dict) -> Result:
        skill_id = await self.repository.find_skill_of_relation(student_id, relation_id)
        if not skill_id:
            return Result.not_found("Relação não encontrada.")

        def change(doc: dict) -> None:
            doc["related"] = [r for r in doc["related"] if r.get("id") != relation_id]

        await self.repository.mutate(student_id, skill_id, change, user)
        return Result.ok(True)


class GenerateSkillRelationsUseCase:
    """A IA escolhe, entre as habilidades do aluno com 1 a 4 estrelas, as que apoiam a finalística. Recebe o grafo em JSON
    anonimizado (+ o contexto anonimizado do aluno) e devolve um JSON; as relações válidas entram no documento do grafo."""

    def __init__(self, repository: ISkillRelationRepository, students: IStudentReader, ai: IAiGateway,
                 prompts: IPromptProvider, settings) -> None:
        self.repository, self.students, self.ai, self.prompts, self.settings = repository, students, ai, prompts, settings

    async def build_request(self, student_id: str, skill_id: str) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        graph = await build_ai_graph(self.repository, student_id, skill_id, with_candidates=True)
        if not graph:
            return Result.not_found("Habilidade não encontrada.")
        if not (await self.repository.skill_info(student_id, skill_id))["finalistic"]:
            return Result.bad_request("Marque a habilidade como finalística antes de gerar as relações.")
        if not graph["candidates"]:
            return Result.bad_request("Não há outras habilidades com 1 a 4 estrelas para relacionar.")
        cfg = resolve_round1_settings(await self.settings.get(SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_SETTINGS))
        extra = {}
        if "diary_summary" in cfg["sources"]:
            extra["diary_summary_since"] = (date.today() - timedelta(days=30 * cfg["diary_summary_months"])).isoformat()
        context, name_map = await self.ai.build_context(student_id, cfg["sources"], **extra)
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== GRAFO (JSON) ===\n{json.dumps(graph, ensure_ascii=False, indent=1)}\n\n"
            f"=== LIMITES ===\nNo máximo {MAX_RELATIONS} relações novas. Use menos quando o caso pedir.\n\nGere o JSON."
        )
        prompt = self.ai.reanonymize(prompt, name_map)  # nomes reais (inclusive dentro das observações) viram o identificador
        system = await self.prompts.get("skill_relations")
        return Result.ok({"system": system, "prompt": prompt, "name_map": name_map, "allowed": {c["code"] for c in graph["candidates"]},
                          "sources": cfg["sources"]})

    async def preview(self, student_id: str, skill_id: str) -> Result:
        built = await self.build_request(student_id, skill_id)
        if not built.is_ok:
            return built
        v = built.value
        return Result.ok({"system": v["system"], "prompt": v["prompt"], "sources": v["sources"]})

    async def execute(self, student_id: str, skill_id: str, user: dict) -> Result:
        built = await self.build_request(student_id, skill_id)
        if not built.is_ok:
            return built
        v = built.value
        raw = None
        for attempt in (1, 2):
            try:
                raw = await self.ai.generate_json("skill_relations", v["system"], v["prompt"], user.get("user_id"))
                break
            except ValueError as e:
                logger.warning("Relações: JSON inválido (aluno %s, tentativa %s): %s", student_id, attempt, e)
                if attempt == 2:
                    return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        by_code = {c["code"]: c for c in await self.repository.candidates(student_id, skill_id) if c["code"] in v["allowed"]}
        picks: list[tuple[dict, str]] = []
        for item in [i for i in (raw.get("relations") or []) if isinstance(i, dict)][:MAX_RELATIONS]:
            target = by_code.get(str(item.get("code") or "").strip())  # anti-alucinação: só candidatas com 1 a 4 estrelas
            if target and all(target["id"] != p[0]["id"] for p in picks):
                picks.append((target, self.ai.deanonymize(str(item.get("reason") or ""), v["name_map"]).strip()))
        created: list[str] = []

        def change(doc: dict) -> None:
            have = {r.get("skill_id") for r in doc["related"]}
            for target, reason in picks:
                if target["id"] in have:
                    continue
                rid = str(uuid.uuid4())
                doc["related"].append({"id": rid, "kind": "skill", "skill_id": target["id"], "direction": "out", "origin": "ai",
                                       "reason": reason, "x": None, "y": None})
                created.append(rid)

        await self.repository.mutate(student_id, skill_id, change, user)
        return Result.ok({"created": len(created), "skipped": len(raw.get("relations") or []) - len(created)})


class GenerateRelationAdaptationsUseCase:
    """2º botão da IA: para cada nó do grafo (habilidade ou campo), escreve adaptação + ações e grava no mesmo JSON.
    Não sobrescreve o que a professora editou à mão (adaptation_origin == "manual")."""

    def __init__(self, repository: ISkillRelationRepository, students: IStudentReader, ai: IAiGateway,
                 prompts: IPromptProvider, settings) -> None:
        self.repository, self.students, self.ai, self.prompts, self.settings = repository, students, ai, prompts, settings

    async def execute(self, student_id: str, skill_id: str, user: dict) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        info = await self.repository.skill_info(student_id, skill_id)
        if not info:
            return Result.not_found("Habilidade não encontrada.")
        if not info["finalistic"]:
            return Result.bad_request("Marque a habilidade como finalística antes de gerar as adaptações.")
        doc, _ = await self.repository.get_document(student_id, skill_id)
        if not doc["related"]:
            return Result.bad_request("Ligue ao menos uma habilidade à finalística antes de gerar as adaptações.")
        graph = await build_ai_graph(self.repository, student_id, skill_id)
        graph["fields"] = [{"key": r["field_key"], "name": FIELD_NAMES.get(r["field_key"], r["field_key"]), "reason": r.get("reason") or ""}
                           for r in doc["related"] if r.get("kind") == "field" and r.get("field_key")]
        cfg = resolve_round1_settings(await self.settings.get(SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_SETTINGS))
        extra = {}
        if "diary_summary" in cfg["sources"]:
            extra["diary_summary_since"] = (date.today() - timedelta(days=30 * cfg["diary_summary_months"])).isoformat()
        context, name_map = await self.ai.build_context(student_id, cfg["sources"], **extra)
        prompt = self.ai.reanonymize(
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== GRAFO (JSON) ===\n{json.dumps(graph, ensure_ascii=False, indent=1)}\n\nGere o JSON.", name_map)
        system = await self.prompts.get("skill_adaptations")
        raw = None
        for attempt in (1, 2):
            try:
                raw = await self.ai.generate_json("skill_adaptations", system, prompt, user.get("user_id"))
                break
            except ValueError as e:
                logger.warning("Adaptações: JSON inválido (aluno %s, tentativa %s): %s", student_id, attempt, e)
                if attempt == 2:
                    return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        briefs = await self.repository.skill_briefs(student_id, [r["skill_id"] for r in doc["related"] if r.get("skill_id")])
        by_ref: dict[str, str] = {}  # código (ou chave do campo) -> id da relação
        for r in doc["related"]:
            ref = r.get("field_key") if r.get("kind") == "field" else (briefs.get(r.get("skill_id")) or {}).get("code")
            if ref:
                by_ref[str(ref)] = r["id"]
        picks: dict[str, tuple[str, list[str]]] = {}
        for item in [i for i in (raw.get("adaptations") or []) if isinstance(i, dict)]:
            rid = by_ref.get(str(item.get("code") or "").strip())  # anti-alucinação: só nós que existem no grafo
            if rid and rid not in picks:
                actions = [self.ai.deanonymize(str(a), name_map).strip() for a in (item.get("actions") or []) if str(a).strip()][:6]
                picks[rid] = (self.ai.deanonymize(str(item.get("adaptation") or ""), name_map).strip(), actions)
        done: list[str] = []

        def change(d: dict) -> None:
            for r in d["related"]:
                if r["id"] in picks and r.get("adaptation_origin") != "manual" and picks[r["id"]][0]:
                    r["adaptation"], r["actions"] = picks[r["id"]]
                    r["adaptation_origin"] = "ai"
                    done.append(r["id"])

        await self.repository.mutate(student_id, skill_id, change, user)
        return Result.ok({"adapted": len(done), "skipped": len(doc["related"]) - len(done)})
