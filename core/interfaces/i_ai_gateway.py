from abc import ABC, abstractmethod


class IAiGateway(ABC):
    """Porta de saída para IA generativa + contexto anonimizado do aluno.

    A camada de aplicação depende só desta interface; a implementação (Gemini, anonimização,
    log de uso) fica em infrastructure."""

    @abstractmethod
    async def build_context(self, student_id: str, sources: list[str]) -> tuple[str, dict[str, str]]:
        """Contexto anonimizado do aluno e o mapa id-anônimo → nome real."""

    @abstractmethod
    async def generate_json(
        self, operation: str, system_instruction: str, prompt: str, user_id: str | None,
        with_bncc_catalog: bool = False,
    ) -> dict:
        """Chama o modelo, registra o uso e devolve o JSON. Lança ValueError se a resposta não for JSON."""

    @abstractmethod
    def deanonymize(self, text: str, name_map: dict[str, str]) -> str:
        ...

    @abstractmethod
    def reanonymize(self, text: str, name_map: dict[str, str]) -> str:
        ...
