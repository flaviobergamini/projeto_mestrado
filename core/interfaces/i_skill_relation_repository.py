from abc import ABC, abstractmethod
from typing import Optional


class SkillRelationError(Exception):
    """Regra violada ao criar/alterar uma relação (mensagem em português para o usuário)."""


class ISkillRelationRepository(ABC):
    @abstractmethod
    async def overview(self, student_id: str) -> list[dict]:
        """Habilidades do aluno que têm relações ou estão marcadas como indiretas (para a lista do mapa)."""

    @abstractmethod
    async def list_relations(self, student_id: str, skill_id: str) -> list[dict]: ...

    @abstractmethod
    async def skill_info(self, student_id: str, skill_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def resolve_codes(self, codes: list[str]) -> dict[str, dict]:
        """{código: {id, code, grade, area, description}} das habilidades existentes."""

    @abstractmethod
    async def create(self, student_id: str, skill_id: str, data: dict, user: dict, source: str) -> dict: ...

    @abstractmethod
    async def update(self, student_id: str, relation_id: str, data: dict) -> dict: ...

    @abstractmethod
    async def delete(self, student_id: str, relation_id: str) -> bool: ...
