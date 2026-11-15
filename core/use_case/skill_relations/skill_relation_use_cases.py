"""Relações entre habilidades: listar, criar/editar/apagar à mão e gerar com IA. Regra aqui; HTTP nas rotas."""
import logging
from datetime import date, timedelta
from typing import Optional

from core.constants.bncc_fields import EXPERIENCE_FIELDS, EXPERIENCE_FIELD_NAMES_PT
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_prompt_provider import IPromptProvider
from core.interfaces.i_skill_relation_repository import ISkillRelationRepository, SkillRelationError
from core.interfaces.i_student_reader import IStudentReader
from core.kernel.result import Result
from core.use_case.skill_plan.prompts import SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_SETTINGS, resolve_round1_settings

logger = logging.getLogger(__name__)

MAX_RELATIONS = 6  # teto de relações novas por geração (a IA usa menos quando o caso pede)


class SkillRelationUseCases:
    """Operações simples sobre as relações de uma habilidade."""

    def __init__(self, repository: ISkillRelationRepository) -> None:
        self.repository = repository

    async def overview(self, student_id: str) -> Result:
        return Result.ok(await self.repository.overview(student_id))

    async def list_relations(self, student_id: str, skill_id: str) -> Result:
        info = await self.repository.skill_info(student_id, skill_id)
        if not info:
            return Result.not_found("Habilidade não encontrada.")
        return Result.ok({"skill": info, "relations": await self.repository.list_relations(student_id, skill_id)})

    async def create(self, student_id: str, skill_id: str, data: dict, user: dict) -> Result:
        try:
            return Result.ok(await self.repository.create(student_id, skill_id, data, user, "manual"))
        except SkillRelationError as e:
            return Result.bad_request(str(e))

    async def update(self, student_id: str, relation_id: str, data: dict) -> Result:
        try:
            return Result.ok(await self.repository.update(student_id, relation_id, data))
        except SkillRelationError as e:
            return Result.not_found(str(e))

    async def delete(self, student_id: str, relation_id: str) -> Result:
        return Result.ok(True) if await self.repository.delete(student_id, relation_id) else Result.not_found("Relação não encontrada.")


class GenerateSkillRelationsUseCase:
    """A IA relaciona UMA habilidade do aluno com outras habilidades da BNCC e com campos de experiência (Educação Infantil),
    propondo para cada relação a adaptação, a justificativa e as ações práticas. Só acrescenta: relações que já existem
    não são repetidas nem sobrescritas. Usa as mesmas fontes de contexto configuradas para a geração das adaptações."""

    def __init__(self, repository: ISkillRelationRepository, students: IStudentReader, ai: IAiGateway,
                 prompts: IPromptProvider, settings) -> None:
        self.repository, self.students, self.ai, self.prompts, self.settings = repository, students, ai, prompts, settings

    async def build_request(self, student_id: str, skill_id: str) -> Result:
        if not await self.students.get_by_id(student_id):
            return Result.not_found("Aluno não encontrado.")
        skill = await self.repository.skill_info(student_id, skill_id)
        if not skill:
            return Result.not_found("Habilidade não encontrada.")
        cfg = resolve_round1_settings(await self.settings.get(SKILL_PLAN_SETTINGS_KEY, DEFAULT_SKILL_PLAN_SETTINGS))
        extra = {}
        if "diary_summary" in cfg["sources"]:
            extra["diary_summary_since"] = (date.today() - timedelta(days=30 * cfg["diary_summary_months"])).isoformat()
        context, name_map = await self.ai.build_context(student_id, cfg["sources"], **extra)
        existing = await self.repository.list_relations(student_id, skill_id)
        already = "\n".join(
            f"- {(r['related_skill'] or {}).get('code') or EXPERIENCE_FIELD_NAMES_PT.get(r['field_key'] or '', r['field_key'])}"
            for r in existing) or "(nenhuma)"
        fields = "\n".join(f"- {key}: {name}" for key, name in EXPERIENCE_FIELD_NAMES_PT.items())
        direct = ("ATENÇÃO: esta habilidade está marcada como NÃO TRABALHAR DIRETAMENTE: ela nunca vira adaptação própria, "
                  "só se trabalha por meio das relações abaixo.\n" if skill["indirect_only"] else "")
        prompt = (
            f"ID do aluno (anonimizado): {student_id}\n\n=== CONTEXTO ===\n{context}\n\n"
            f"=== HABILIDADE A RELACIONAR ===\n{skill['code']} ({skill['grade']}, {skill['area']}): {skill['description']} | "
            f"nota atual: {skill['score']} de 5 estrelas\n{direct}\n"
            f"=== RELAÇÕES JÁ EXISTENTES (não repetir) ===\n{already}\n\n"
            f"=== CAMPOS DE EXPERIÊNCIA (chave: nome) ===\n{fields}\n\n"
            f"=== LIMITES ===\nNo máximo {MAX_RELATIONS} relações novas e {cfg['max_actions']} ação(ões) por relação. "
            f"Use menos quando o caso pedir.\n\nGere o JSON."
        )
        prompt = self.ai.reanonymize(prompt, name_map)
        system = await self.prompts.get("skill_relations")
        return Result.ok({"system": system, "prompt": prompt, "name_map": name_map, "skill": skill,
                          "max_actions": cfg["max_actions"], "sources": cfg["sources"]})

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
                raw = await self.ai.generate_json("skill_relations", v["system"], v["prompt"], user.get("user_id"),
                                                  with_bncc_catalog=True)
                break
            except ValueError as e:
                logger.warning("Relações: JSON inválido (aluno %s, tentativa %s): %s", student_id, attempt, e)
                if attempt == 2:
                    return Result.err(f"A IA não devolveu JSON válido ({e}). Tente novamente.")

        items = [i for i in (raw.get("relations") or []) if isinstance(i, dict)][:MAX_RELATIONS]
        codes = [str(i.get("code")).strip() for i in items if i.get("kind") == "skill" and i.get("code")]
        known = await self.repository.resolve_codes(codes)  # anti-alucinação: só códigos que existem no catálogo
        created, skipped = [], 0
        for item in items:
            actions = [self.ai.deanonymize(str(a), v["name_map"]) for a in (item.get("actions") or []) if str(a).strip()]
            data = {
                "adaptation": self.ai.deanonymize(str(item.get("adaptation") or ""), v["name_map"]),
                "justification": self.ai.deanonymize(str(item.get("justification") or ""), v["name_map"]),
                "actions": actions[:v["max_actions"]],
            }
            if not data["adaptation"].strip() or not data["actions"]:
                skipped += 1
                continue
            if item.get("kind") == "skill":
                target = known.get(str(item.get("code") or "").strip())
                if not target:
                    skipped += 1
                    continue
                data.update(kind="skill", related_skill_id=target["id"])
            elif item.get("kind") == "field" and item.get("field") in EXPERIENCE_FIELDS:
                data.update(kind="field", field_key=item["field"])
            else:
                skipped += 1
                continue
            try:
                created.append(await self.repository.create(student_id, skill_id, data, user, "ai"))
            except SkillRelationError:
                skipped += 1  # relação repetida ou inválida
        return Result.ok({"created": len(created), "skipped": skipped, "relations": created})
