from abc import ABC, abstractmethod
from typing import Optional


class IUserRepository(ABC):

    @abstractmethod
    async def add(self, id: str, username: str, full_name: Optional[str], role: str,
                  municipality_id: Optional[str], school_id: Optional[str],
                  teacher_id: Optional[str], is_active: bool) -> dict:
        ...

    @abstractmethod
    async def update_role(self, user_id: str, role: str) -> dict:
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def get_all(self) -> list[dict]:
        ...
