from core.kernel.result import Result
from core.interfaces.i_links_repository import ILinksRepository
from core.interfaces.i_teacher_reader import ITeacherReader


class ListStudentsWithLinksUseCase:
    def __init__(self, repository: ILinksRepository) -> None:
        self.repository = repository

    async def execute(self, page: int, page_size: int, name: str | None) -> Result:
        return Result.ok(await self.repository.list_students_with_links(page=page, page_size=page_size, name_filter=name))


class ListLinkableTeachersUseCase:
    def __init__(self, teachers: ITeacherReader) -> None:
        self.teachers = teachers

    async def execute(self) -> Result:
        return Result.ok(await self.teachers.list_all())


class SetStudentTeachersUseCase:
    """Substitui todos os professores vinculados a um aluno."""

    def __init__(self, repository: ILinksRepository) -> None:
        self.repository = repository

    async def execute(self, student_id: str, teacher_ids: list[str]) -> Result:
        if not await self.repository.set_student_teachers(student_id, teacher_ids):
            return Result.not_found("Aluno não encontrado")
        return Result.ok({"ok": True})


class SetTeacherStudentsUseCase:
    """Substitui todos os alunos vinculados a um professor."""

    def __init__(self, repository: ILinksRepository) -> None:
        self.repository = repository

    async def execute(self, teacher_id: str, student_ids: list[str]) -> Result:
        if not await self.repository.set_teacher_students(teacher_id, student_ids):
            return Result.not_found("Professor não encontrado")
        return Result.ok({"ok": True})


class GetRelationsUseCase:
    def __init__(self, repository: ILinksRepository) -> None:
        self.repository = repository

    async def execute(self) -> Result:
        return Result.ok(await self.repository.relations())
