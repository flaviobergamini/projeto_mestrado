from abc import ABC, abstractmethod
from typing import Callable, Optional


class SkillRelationError(Exception):
    """Regra violada ao criar/alterar uma relação (mensagem em português para o usuário)."""


class ISkillRelationRepository(ABC):
    """Persistência do grafo de relações: UM documento JSON por aluno + habilidade finalística.

    Documento: {"schema": 1, "related": [{"id", "skill_id", "direction": "both"|"out"|"in", "origin": "ai"|"manual", "reason", "x", "y"}]}
    Só estrutura; estrelas e observações são lidas das notas do aluno na hora de montar a visão."""

    @abstractmethod
    async def overview(self, student_id: str) -> list[dict]:
        """Habilidades do aluno com 1 a 4 estrelas, com a marca de finalística, o nº de relações visíveis e a data da nota."""

    @abstractmethod
    async def get_document(self, student_id: str, skill_id: str) -> tuple[dict, int]:
        """(documento, revisão). Sem documento ainda: ({"schema": 1, "related": []}, 0)."""

    @abstractmethod
    async def mutate(self, student_id: str, skill_id: str, change: Callable[[dict], None], user: dict) -> tuple[dict, int]:
        """Aplica `change(documento)` de forma atômica (trava a linha), sobe a revisão e devolve (documento, revisão).
        `change` pode levantar SkillRelationError para abortar sem gravar."""

    @abstractmethod
    async def find_skill_of_relation(self, student_id: str, relation_id: str) -> Optional[str]:
        """skill_id (finalística) do documento que contém a relação."""

    @abstractmethod
    async def skill_info(self, student_id: str, skill_id: str) -> Optional[dict]: ...

    @abstractmethod
    async def skill_briefs(self, student_id: str, skill_ids: list[str]) -> dict[str, dict]:
        """{skill_id: {id, code, grade, area, description, score, observation}} com a nota ATUAL do aluno."""

    @abstractmethod
    async def plan_adaptations(self, student_id: str, skill_id: str) -> list[dict]:
        """Adaptações do plano da habilidade (finalística): [{id, adaptation, justification, actions: [{id, action}]}]."""

    @abstractmethod
    async def save_finalistic_adaptation(self, student_id: str, skill_id: str, group_id: Optional[str], adaptation: str,
                                         justification: str, actions: list[str]) -> str:
        """Grava UMA adaptação no plano da finalística (atualiza a de `group_id`, senão cria) e devolve o id dela."""

    @abstractmethod
    async def candidates(self, student_id: str, exclude_skill_id: str) -> list[dict]:
        """Habilidades do aluno com 1 a 4 estrelas (as únicas que podem entrar no grafo), com a observação de cada uma."""
