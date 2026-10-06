"""Use cases do perfil funcional."""
import logging
from typing import Optional
from core.constants.functional_profile import DOMAINS, LEVEL_SCALE, DEFAULT_SOURCES
from core.kernel.result import Result
from core.interfaces.i_ai_gateway import IAiGateway
from core.interfaces.i_bncc_repository import IBnccRepository
from core.interfaces.i_functional_profile_repository import IFunctionalProfileRepository, ProfileError
from core.interfaces.i_student_reader import IStudentReader
from core.services.functional_profile_content import normalize_content, map_strings
from core.use_case.functional_profile.prompts import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

NOT_FOUND = "Perfil não encontrado"


class ListFunctionalDomainsUseCase:
    async def execute(self) -> Result:
        return Result.ok({"domains": [{"key": k, "label": v} for k, v in DOMAINS], "scale": LEVEL_SCALE})


class GenerateFunctionalProfileUseCase:
    """Gera o perfil funcional com IA a partir do contexto anonimizado do aluno."""

    def __init__(self, repository: IFunctionalProfileRepository, students: IStudentReader,
                 bncc: IBnccRepository, ai: IAiGateway) -> None:
        self.repository = repository
        self.students = students
        self.bncc = bncc
        self.ai = ai

    async def execute(self, student_id: str, user: dict, sources: Optional[list[str]] = None,
                      period_start: Optional[str] = None, period_end: Optional[str] = None,
                      notes: Optional[str] = None) -> Result:
        student = await self.students.get_by_id(student_id)
        if not student:
            return Result.not_found("Aluno não encontrado.")

        # O perfil funcional nunca usa a si mesmo como fonte.
        chosen = [s for s in (sources or DEFAULT_SOURCES) if s != "functional_profile"] or DEFAULT_SOURCES
        context, name_map = await self.ai.build_context(student_id, chosen)
        prompt = self._prompt(student_id, student.get("school_id"), context, period_start, period_end, notes)

        raw: dict = {}
        last_error = ""
        for attempt in range(2):
            attempt_prompt = prompt if attempt == 0 else (
                prompt + "\n\nATENÇÃO: sua resposta anterior não era um JSON válido. Responda apenas com o objeto JSON."
            )
            try:
                raw = await self.ai.generate_json(
                    "functional_profile_generation", SYSTEM_INSTRUCTION, attempt_prompt, user.get("user_id"),
                    with_bncc_catalog="bncc_catalog" in chosen,
                )
                break
            except ValueError as e:
                last_error = str(e)
                logger.warning("Perfil funcional: JSON inválido (aluno %s, tentativa %d): %s", student_id, attempt + 1, e)
        else:
            return Result.err(f"A IA não devolveu um perfil válido ({last_error}). Tente novamente.")

        # Desanonimiza (ID → nome real) cada texto do perfil, como é feito no PEI.
        content = map_strings(normalize_content(raw), lambda s: self.ai.deanonymize(s, name_map))
        # Anti-alucinação: só ficam referências a códigos que realmente existem no catálogo.
        valid_codes = set(await self.bncc.list_codes())
        for d in content["domains"]:
            d["bncc_references"] = [c for c in d["bncc_references"] if c in valid_codes]
        try:
            return Result.ok(await self.repository.create(
                student_id, content, "ai", user, period_start=period_start, period_end=period_end, sources=chosen,
            ))
        except ProfileError as e:
            return Result.bad_request(str(e))

    @staticmethod
    def _prompt(student_id: str, school_id: Optional[str], context: str, period_start: Optional[str],
                period_end: Optional[str], notes: Optional[str]) -> str:
        period = ""
        if period_start or period_end:
            period = f"\nPeríodo de referência do perfil: {period_start or '?'} a {period_end or '?'}."
        extra = f"\nOrientações do avaliador: {notes.strip()}" if notes and notes.strip() else ""
        return (
            "DADOS DO ALUNO (ANONIMIZADOS) — copie o identificador EXATAMENTE como fornecido ao citar o aluno ou a escola:\n"
            f"- ID do aluno: {student_id}\n- ID da escola: {school_id or '(não informado)'}{period}{extra}\n\n"
            f"=== CONTEXTO DO ALUNO (ANONIMIZADO) ===\n{context}\n\n"
            "Elabore agora o perfil funcional em JSON."
        )


class CreateManualProfileUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: Optional[str], content: Optional[dict], user: dict, title: Optional[str],
                      period_start: Optional[str], period_end: Optional[str]) -> Result:
        if not student_id:
            return Result.bad_request("Informe o aluno.")
        try:
            return Result.ok(await self.repository.create(
                student_id, content or {}, "manual", user, title=title,
                period_start=period_start, period_end=period_end,
            ))
        except ProfileError as e:
            return Result.bad_request(str(e))


class ListStudentProfilesUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str) -> Result:
        return Result.ok(await self.repository.list_for_student(student_id))


class GetProfileEvolutionUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str) -> Result:
        return Result.ok(await self.repository.evolution(student_id))


class GetProfileUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, profile_id: str) -> Result:
        profile = await self.repository.get(profile_id)
        return Result.ok(profile) if profile else Result.not_found(NOT_FOUND)


class UpdateProfileUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, profile_id: str, content: Optional[dict], user: dict, title: Optional[str],
                      period_start: Optional[str], period_end: Optional[str], fields_set: set) -> Result:
        try:
            updated = await self.repository.update(
                profile_id, content, user, title=title, period_start=period_start,
                period_end=period_end, fields_set=fields_set,
            )
        except ProfileError as e:
            return Result.bad_request(str(e))
        return Result.ok(updated) if updated else Result.not_found(NOT_FOUND)


class DeleteProfileUseCase:
    def __init__(self, repository: IFunctionalProfileRepository) -> None:
        self.repository = repository

    async def execute(self, profile_id: str) -> Result:
        return Result.ok(True) if await self.repository.delete(profile_id) else Result.not_found(NOT_FOUND)
