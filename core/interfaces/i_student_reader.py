from abc import ABC, abstractmethod
from typing import Optional


class IStudentReader(ABC):

    @abstractmethod
    async def get_by_id(self, student_id: str) -> Optional[dict]:
        ...
