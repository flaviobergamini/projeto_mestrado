"""Use cases do módulo BNCC (catálogo, notas por aluno e relatórios)."""
from typing import Optional
from core.kernel.result import Result
from core.interfaces.i_bncc_repository import IBnccRepository, BnccError
from core.interfaces.i_report_pdf_generator import IReportPdfGenerator
from core.interfaces.i_student_reader import IStudentReader

SKILL_NOT_FOUND = "Habilidade não encontrada"
REPORT_NOT_FOUND = "Relatório não encontrado"


class _BnccUseCase:
    def __init__(self, repository: IBnccRepository) -> None:
        self.repository = repository


class ListGradesUseCase(_BnccUseCase):
    async def execute(self) -> Result:
        return Result.ok(await self.repository.list_grades())


class ListAreasUseCase(_BnccUseCase):
    async def execute(self) -> Result:
        return Result.ok(await self.repository.list_areas())


class ListSkillsUseCase(_BnccUseCase):
    async def execute(self, grades: Optional[list[str]], areas: Optional[list[str]], q: Optional[str]) -> Result:
        return Result.ok(await self.repository.list_skills(grades, areas, q))


class CreateSkillUseCase(_BnccUseCase):
    async def execute(self, data: dict) -> Result:
        try:
            return Result.ok(await self.repository.create_skill(data))
        except BnccError as e:
            return Result.bad_request(str(e))


class UpdateSkillUseCase(_BnccUseCase):
    async def execute(self, skill_id: str, data: dict) -> Result:
        try:
            updated = await self.repository.update_skill(skill_id, data)
        except BnccError as e:
            return Result.bad_request(str(e))
        return Result.ok(updated) if updated else Result.not_found(SKILL_NOT_FOUND)


class DeleteSkillUseCase(_BnccUseCase):
    async def execute(self, skill_id: str) -> Result:
        return Result.ok(True) if await self.repository.delete_skill(skill_id) else Result.not_found(SKILL_NOT_FOUND)


class ListStudentSkillsUseCase(_BnccUseCase):
    async def execute(self, student_id: str, **filters) -> Result:
        return Result.ok(await self.repository.student_skills(student_id, **filters))


class SetSkillScoreUseCase(_BnccUseCase):
    async def execute(self, student_id: str, skill_id: str, fields: dict, user: dict) -> Result:
        try:
            return Result.ok(await self.repository.set_score(student_id, skill_id, fields, user))
        except BnccError as e:
            return Result.not_found(str(e))


class ListSkillEventsUseCase(_BnccUseCase):
    async def execute(self, student_id: str, skill_id: str) -> Result:
        return Result.ok(await self.repository.list_events(student_id, skill_id))


class CreateSkillReportUseCase(_BnccUseCase):
    async def execute(self, student_id: str, filters: dict, user: dict) -> Result:
        try:
            return Result.ok(await self.repository.create_report(student_id, filters, user))
        except BnccError as e:
            return Result.not_found(str(e))


class ListSkillReportsUseCase(_BnccUseCase):
    async def execute(self, student_id: str) -> Result:
        return Result.ok(await self.repository.list_reports(student_id))


class GetSkillReportUseCase(_BnccUseCase):
    async def execute(self, report_id: str) -> Result:
        report = await self.repository.get_report(report_id)
        return Result.ok(report) if report else Result.not_found(REPORT_NOT_FOUND)


class DeleteSkillReportUseCase(_BnccUseCase):
    async def execute(self, report_id: str) -> Result:
        return Result.ok(True) if await self.repository.delete_report(report_id) else Result.not_found(REPORT_NOT_FOUND)


class RenderSkillReportPdfUseCase:
    def __init__(self, repository: IBnccRepository, students: IStudentReader, pdf: IReportPdfGenerator) -> None:
        self.repository = repository
        self.students = students
        self.pdf = pdf

    async def execute(self, report_id: str) -> Result:
        report = await self.repository.get_report(report_id)
        if not report:
            return Result.not_found(REPORT_NOT_FOUND)
        student = await self.students.get_by_id(report["student_id"])
        return Result.ok(self.pdf.skill_report(report, (student or {}).get("name") or "Aluno"))
