from abc import ABC, abstractmethod
from typing import Optional


class ISkillPlanRepository(ABC):

    @abstractmethod
    async def plan_skills(self, student_id: str) -> list[dict]:
        """Habilidades no PDI do aluno que a IA pode trabalhar (não marcadas como 'sem IA')."""

    @abstractmethod
    async def apply_round1(self, student_id: str, drafts: dict[str, dict], user: dict) -> list[str]:
        """Grava rascunhos apenas em campos vazios; devolve os skill_ids alterados."""

    @abstractmethod
    async def cards_by_skill(self, student_id: str, skill_ids: list[str]) -> dict[str, list[dict]]:
        ...

    @abstractmethod
    async def replace_pending_suggestions(self, student_id: str, items: list[dict]) -> list[dict]:
        ...

    @abstractmethod
    async def list_suggestions(self, student_id: str, status: str = "pending") -> list[dict]:
        ...

    @abstractmethod
    async def decide(self, suggestion_id: str, accept: bool, user: dict) -> Optional[dict]:
        ...
