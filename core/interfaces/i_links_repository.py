from abc import ABC, abstractmethod
from typing import Optional


class ILinksRepository(ABC):

    @abstractmethod
    async def list_students_with_links(
        self, page: int = 1, page_size: int = 20, name_filter: Optional[str] = None,
    ) -> dict:
        ...

    @abstractmethod
    async def set_student_teachers(self, student_id: str, teacher_ids: list[str]) -> bool:
        ...

    @abstractmethod
    async def set_teacher_students(self, teacher_id: str, student_ids: list[str]) -> bool:
        ...

    @abstractmethod
    async def relations(self) -> dict:
        """Escolas por município, professores por escola (com alunos) e alunos por escola/professor."""
