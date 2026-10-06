from abc import ABC, abstractmethod
from typing import Optional


class IKanbanRepository(ABC):

    @abstractmethod
    async def list_by_student(self, student_id: str) -> list[dict]: ...

    @abstractmethod
    async def create(self, data: dict) -> dict: ...

    @abstractmethod
    async def update(self, card_id: str, data: dict) -> Optional[dict]: ...

    @abstractmethod
    async def delete(self, card_id: str) -> bool: ...

    @abstractmethod
    async def create_from_skill(self, student_id: str, skill_id: str, created_by: Optional[str] = None) -> list[dict]: ...
