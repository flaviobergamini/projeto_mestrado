from abc import ABC, abstractmethod


class IPromptProvider(ABC):

    @abstractmethod
    async def get(self, scope: str) -> str:
        """Texto do prompt ativo do escopo (o do administrador, ou o padrão)."""
