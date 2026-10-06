from abc import ABC, abstractmethod


class ITeacherReader(ABC):

    @abstractmethod
    async def list_all(self) -> list[dict]:
        ...
