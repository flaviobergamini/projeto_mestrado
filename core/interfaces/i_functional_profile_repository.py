from abc import ABC, abstractmethod
from typing import Optional


class ProfileError(ValueError):
    """Regra do perfil funcional violada (aluno inexistente, período inválido...)."""


class IFunctionalProfileRepository(ABC):

    @abstractmethod
    async def create(self, student_id: str, content: dict, origin: str, user: dict, title: Optional[str] = None,
                     period_start: Optional[str] = None, period_end: Optional[str] = None,
                     sources: Optional[list[str]] = None) -> dict: ...

    @abstractmethod
    async def update(self, profile_id: str, content: Optional[dict], user: dict, title: Optional[str] = None,
                     period_start: Optional[str] = None, period_end: Optional[str] = None,
                     fields_set: Optional[set] = None) -> Optional[dict]: ...

    @abstractmethod
    async def list_for_student(self, student_id: str) -> list[dict]: ...

    @abstractmethod
    async def get(self, profile_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def delete(self, profile_id: str) -> bool: ...

    @abstractmethod
    async def evolution(self, student_id: str) -> dict: ...
