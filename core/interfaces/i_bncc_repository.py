from abc import ABC, abstractmethod
from typing import Optional


class BnccError(ValueError):
    """Violação de regra do catálogo/notas BNCC (dado inválido, duplicidade, registro inexistente)."""


class IBnccRepository(ABC):

    # catálogo
    @abstractmethod
    async def list_grades(self) -> list[dict]: ...

    @abstractmethod
    async def list_codes(self) -> list[str]: ...

    @abstractmethod
    async def list_areas(self) -> list[str]: ...

    @abstractmethod
    async def list_skills(self, grades: Optional[list[str]] = None, areas: Optional[list[str]] = None,
                          q: Optional[str] = None) -> list[dict]: ...

    @abstractmethod
    async def create_skill(self, data: dict) -> dict: ...

    @abstractmethod
    async def update_skill(self, skill_id: str, data: dict) -> Optional[dict]: ...

    @abstractmethod
    async def delete_skill(self, skill_id: str) -> bool: ...

    # notas por aluno
    @abstractmethod
    async def student_skills(self, student_id: str, grades: Optional[list[str]] = None,
                             areas: Optional[list[str]] = None, q: Optional[str] = None,
                             min_score: Optional[int] = None, max_score: Optional[int] = None,
                             only_with_observation: bool = False, only_in_plan: bool = False) -> list[dict]: ...

    @abstractmethod
    async def set_score(self, student_id: str, skill_id: str, fields: dict, user: dict) -> dict: ...

    @abstractmethod
    async def list_events(self, student_id: str, skill_id: str) -> list[dict]: ...

    # relatórios
    @abstractmethod
    async def create_report(self, student_id: str, filters: dict, user: dict) -> dict: ...

    @abstractmethod
    async def list_reports(self, student_id: str) -> list[dict]: ...

    @abstractmethod
    async def get_report(self, report_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def delete_report(self, report_id: str) -> bool: ...
